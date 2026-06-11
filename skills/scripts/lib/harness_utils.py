"""Shared helpers for harness-kit scripts.

Standard library only. Provides:
    * Path resolution (SKILL_ROOT, TEMPLATE_DIR)
    * Template copy with {{KEY}} substitution
    * Workspace inspection (file loading, governance vs code split)
    * 5-subsystem scoring (Instructions, State, Verification, Scope, Lifecycle)
    * Text reports and self-contained HTML reports
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

SKILL_ROOT: Path = Path(__file__).resolve().parents[2]
TEMPLATE_DIR: Path = SKILL_ROOT / "templates"

SUBSYSTEMS: Tuple[str, ...] = (
    "instructions",
    "state",
    "verification",
    "scope",
    "lifecycle",
)

CODE_TEMPLATES: Tuple[str, ...] = (
    "harness.py",
    "context_manager.py",
    "tool_registry.py",
    "persistence.py",
    "hooks.py",
    "subagent.py",
    "prompt_assembly.py",
)

GOVERNANCE_TEMPLATES: Tuple[str, ...] = (
    "AGENTS.md",
    "feature_list.json",
    "feature-list.schema.json",
    "progress.md",
    "session-handoff.md",
    "init.sh",
    "init.ps1",
)


# --------------------------------------------------------------------------- #
# Filesystem helpers
# --------------------------------------------------------------------------- #


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def make_executable(path: Path) -> None:
    """Best-effort chmod +x. No-op on Windows for non-cygwin runs."""
    try:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass


# --------------------------------------------------------------------------- #
# Template rendering
# --------------------------------------------------------------------------- #


_PLACEHOLDER = re.compile(r"\{\{\s*([A-Z][A-Z0-9_]*)\s*\}\}")


def render(template: str, replacements: Dict[str, str]) -> str:
    """Replace every ``{{KEY}}`` token in ``template`` with ``replacements[KEY]``.

    Unknown keys are left in place so a missed substitution stays visible
    rather than silently dropping content.
    """

    def sub(match: re.Match) -> str:
        key = match.group(1)
        return replacements.get(key, match.group(0))

    return _PLACEHOLDER.sub(sub, template)


@dataclass
class CopyResult:
    name: str
    path: Path
    status: str  # "written" | "skipped"
    reason: str = ""


def copy_template(
    name: str,
    dest: Path,
    *,
    replacements: Optional[Dict[str, str]] = None,
    force: bool = False,
    rename_to: Optional[str] = None,
) -> CopyResult:
    """Copy a single template into ``dest`` (a directory), applying substitution.

    ``rename_to`` lets the caller emit the template under a different name
    (e.g., rename ``AGENTS.md`` -> ``CLAUDE.md``).
    """
    src = TEMPLATE_DIR / name
    target_name = rename_to or name
    out = dest / target_name

    if out.exists() and not force:
        return CopyResult(
            name=name, path=out, status="skipped", reason="already exists"
        )

    if not src.exists():
        return CopyResult(
            name=name, path=out, status="skipped", reason="template missing"
        )

    out.parent.mkdir(parents=True, exist_ok=True)

    raw = src.read_text(encoding="utf-8")
    rendered = render(raw, replacements or {})
    out.write_text(rendered, encoding="utf-8")

    if out.suffix == ".sh":
        make_executable(out)

    return CopyResult(name=name, path=out, status="written")


# --------------------------------------------------------------------------- #
# Workspace inspection
# --------------------------------------------------------------------------- #


GOVERNANCE_CANDIDATES: Tuple[str, ...] = (
    "AGENTS.md",
    "CLAUDE.md",
    "feature_list.json",
    "feature-list.json",
    "progress.md",
    "session-handoff.md",
    "init.sh",
    "init.ps1",
    "init.bat",
    "init.cmd",
)


def load_governance(root: Path) -> Dict[str, str]:
    """Read every governance file that exists under ``root`` into a dict."""
    out: Dict[str, str] = {}
    for name in GOVERNANCE_CANDIDATES:
        path = root / name
        if path.is_file():
            try:
                out[name] = path.read_text(encoding="utf-8")
            except OSError:
                continue
    return out


def list_code_modules(harness_dir: Path) -> Dict[str, bool]:
    """Return which CODE_TEMPLATES exist under ``harness_dir``."""
    return {name: (harness_dir / name).is_file() for name in CODE_TEMPLATES}


# --------------------------------------------------------------------------- #
# Text matching (word-bounded)
# --------------------------------------------------------------------------- #


def _compile_needle(needle: str) -> re.Pattern:
    """Build a case-insensitive, word-bounded matcher for ``needle``.

    Word boundaries fall back to plain substring when ``needle`` starts or
    ends with a non-word character (so patterns like ``$ErrorActionPreference``
    or ``./init.sh`` still match).
    """
    escaped = re.escape(needle)
    left = r"\b" if needle[:1].isalnum() or needle[:1] == "_" else ""
    right = r"\b" if needle[-1:].isalnum() or needle[-1:] == "_" else ""
    return re.compile(left + escaped + right, re.IGNORECASE)


def text_has(text: str, needles: Iterable[str]) -> bool:
    if not text:
        return False
    for needle in needles:
        if _compile_needle(needle).search(text):
            return True
    return False


def has_file(files: Dict[str, str], names: Iterable[str]) -> bool:
    return any(name in files for name in names)


# --------------------------------------------------------------------------- #
# Feature list validation
# --------------------------------------------------------------------------- #


_FEATURE_ID_RE = re.compile(r"^F-\d+$|^feat-\d+$", re.IGNORECASE)
_ALLOWED_STATUS = {"pending", "in_progress", "blocked", "done", "not-started", "not_started"}


def validate_feature_list(raw: str) -> Tuple[bool, List[str]]:
    """Check ``raw`` is a feature list JSON document.

    Returns ``(ok, errors)``. ``errors`` lists every violation found so a
    single pass yields actionable feedback.
    """
    errors: List[str] = []
    if not raw.strip():
        return False, ["empty"]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return False, [f"invalid JSON: {exc.msg}"]

    if not isinstance(data, dict):
        return False, ["root must be an object"]

    features = data.get("features")
    if not isinstance(features, list) or not features:
        return False, ["features must be a non-empty array"]

    seen_ids: set = set()
    for idx, feature in enumerate(features):
        prefix = f"features[{idx}]"
        if not isinstance(feature, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for key in ("id", "name", "description", "status"):
            value = feature.get(key)
            if not isinstance(value, str) or not value:
                errors.append(f"{prefix}.{key} missing or not a string")
        fid = feature.get("id", "")
        if fid and not _FEATURE_ID_RE.match(fid):
            errors.append(f"{prefix}.id '{fid}' does not match F-### or feat-###")
        if fid in seen_ids:
            errors.append(f"{prefix}.id '{fid}' duplicated")
        seen_ids.add(fid)
        status = feature.get("status", "")
        if status and status not in _ALLOWED_STATUS:
            errors.append(f"{prefix}.status '{status}' not in {sorted(_ALLOWED_STATUS)}")
        deps = feature.get("dependencies", [])
        if deps is not None and not isinstance(deps, list):
            errors.append(f"{prefix}.dependencies must be an array if present")

    return (not errors), errors


# --------------------------------------------------------------------------- #
# Scoring (5 subsystems × 5 checks)
# --------------------------------------------------------------------------- #


@dataclass
class Check:
    passed: bool
    message: str


@dataclass
class SubsystemResult:
    name: str
    score: int            # 0..5 (no floor)
    passed: int
    total: int
    checks: List[Check] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "passed": self.passed,
            "total": self.total,
            "checks": [{"pass": c.passed, "message": c.message} for c in self.checks],
        }


@dataclass
class ScoreResult:
    overall: int          # 0..100
    bottleneck: str
    subsystems: Dict[str, SubsystemResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "bottleneck": self.bottleneck,
            "subsystems": {n: s.to_dict() for n, s in self.subsystems.items()},
        }


def score_harness(root: Path, harness_dir: Optional[Path] = None) -> ScoreResult:
    """Score a project. ``root`` holds governance; ``harness_dir`` holds code modules.

    If ``harness_dir`` is None we look at ``root / "harness"`` then fall back
    to ``root`` itself so legacy single-folder layouts still score.
    """
    governance = load_governance(root)
    if harness_dir is None:
        candidate = root / "harness"
        harness_dir = candidate if candidate.is_dir() else root
    code = list_code_modules(harness_dir)

    agents_text = governance.get("AGENTS.md", "") or governance.get("CLAUDE.md", "")
    feature_text = (
        governance.get("feature_list.json", "")
        or governance.get("feature-list.json", "")
    )
    progress = governance.get("progress.md", "")
    handoff = governance.get("session-handoff.md", "")
    init_text = ""
    for name in ("init.sh", "init.ps1", "init.bat", "init.cmd"):
        if name in governance:
            init_text = governance[name]
            break

    all_text = "\n\n".join(governance.values())
    feature_valid, _ = validate_feature_list(feature_text) if feature_text else (False, [])

    instructions = [
        Check(has_file(governance, ["AGENTS.md", "CLAUDE.md"]),
              "Agent instruction file exists"),
        Check(text_has(agents_text, ["Startup Workflow", "Before writing code"]),
              "Startup workflow documented"),
        Check(text_has(agents_text, ["Definition of Done", "done only when"]),
              "Definition of Done documented"),
        Check(text_has(agents_text, ["Verification Commands", "./init.sh", "./init.ps1", "verify"]),
              "Verification commands discoverable"),
        Check(text_has(agents_text, ["feature_list.json", "progress.md", "session-handoff.md"]),
              "State artifacts routed from instructions"),
    ]

    state = [
        Check(has_file(governance, ["feature_list.json", "feature-list.json"]),
              "Feature tracker exists"),
        Check(feature_valid, "Feature tracker is valid"),
        Check(has_file(governance, ["progress.md"]),
              "Progress log exists"),
        Check(text_has(progress, ["Current State", "Current Objective", "Next Step", "What I Did"]),
              "Progress log supports restart"),
        Check(text_has(handoff or progress, ["Blockers", "Files", "Next Session"]),
              "Handoff captures blockers, files, and next step"),
    ]

    verification = [
        Check(has_file(governance, ["init.sh", "init.ps1", "init.bat", "init.cmd"]),
              "Verification entrypoint exists"),
        Check(text_has(init_text, ["set -e", "$ErrorActionPreference", "errorlevel", "exit /b"]),
              "Verification fails fast"),
        Check(text_has(init_text + agents_text,
                       ["pytest", "unittest", "vitest", "cargo test", "go test", "dotnet test"]),
              "Test command documented"),
        Check(text_has(init_text + agents_text,
                       ["py_compile", "compileall", "build", "type", "lint", "compile"]),
              "Static / build check documented"),
        Check(text_has(all_text,
                       ["Evidence", "Verification Evidence", "command and output"]),
              "Verification evidence is recorded"),
    ]

    scope = [
        Check(text_has(agents_text, ["One feature at a time", "one-feature-at-a-time"]),
              "One-feature-at-a-time rule exists"),
        Check(text_has(feature_text, ["dependencies"]),
              "Feature dependencies are tracked"),
        Check(text_has(agents_text + feature_text, ["status"]),
              "Feature status is explicit"),
        Check(text_has(agents_text, ["Stay in scope", "Stay in Scope", "scope"]),
              "Scope boundary documented"),
        Check(text_has(agents_text, ["Definition of Done"]),
              "Completion gate limits scope closure"),
    ]

    lifecycle = [
        Check(has_file(governance, ["init.sh", "init.ps1", "init.bat", "init.cmd"]),
              "Startup script exists"),
        Check(text_has(agents_text, ["End of Session", "Before ending"]),
              "End-of-session procedure exists"),
        Check(has_file(governance, ["session-handoff.md"]),
              "Session handoff template exists"),
        Check(text_has(progress + handoff,
                       ["Last Updated", "Current Objective", "Recommended Next Step"]),
              "Session restart markers exist"),
        Check(any(code.values()),
              "Harness code modules scaffolded"),
    ]

    raw: Dict[str, List[Check]] = {
        "instructions": instructions,
        "state": state,
        "verification": verification,
        "scope": scope,
        "lifecycle": lifecycle,
    }

    subsystems: Dict[str, SubsystemResult] = {}
    total = 0
    for name in SUBSYSTEMS:
        checks = raw[name]
        passed = sum(1 for c in checks if c.passed)
        # No floor: a fully empty subsystem scores 0.
        score = round(passed / len(checks) * 5)
        subsystems[name] = SubsystemResult(
            name=name,
            score=score,
            passed=passed,
            total=len(checks),
            checks=checks,
        )
        total += score

    overall = round(total / (len(SUBSYSTEMS) * 5) * 100)

    # Deterministic bottleneck: lowest score, then SUBSYSTEMS order on ties.
    bottleneck = min(
        SUBSYSTEMS,
        key=lambda n: (subsystems[n].score, SUBSYSTEMS.index(n)),
    )

    return ScoreResult(overall=overall, bottleneck=bottleneck, subsystems=subsystems)


# --------------------------------------------------------------------------- #
# Project detection (used by scaffold to seed verification commands)
# --------------------------------------------------------------------------- #


@dataclass
class ProjectInfo:
    stack: str
    has_python: bool
    has_node: bool


def detect_project(root: Path) -> ProjectInfo:
    has_python = any((root / m).exists()
                     for m in ("pyproject.toml", "setup.py", "requirements.txt"))
    has_node = (root / "package.json").exists()
    if has_python and has_node:
        stack = "python+node"
    elif has_python:
        stack = "python"
    elif has_node:
        stack = "node"
    elif (root / "Cargo.toml").exists():
        stack = "rust"
    elif (root / "go.mod").exists():
        stack = "go"
    else:
        stack = "generic"
    return ProjectInfo(stack=stack, has_python=has_python, has_node=has_node)


def primary_verification_command(info: ProjectInfo) -> str:
    if info.stack.startswith("python"):
        return "./init.sh   # POSIX  |  ./init.ps1  Windows"
    return "./init.sh"


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #


def format_text_report(result: ScoreResult, root: Path) -> str:
    out = [
        f"Harness validation for {root}",
        f"Overall: {result.overall}/100",
        f"Bottleneck: {result.bottleneck}",
        "",
    ]
    for name in SUBSYSTEMS:
        sub = result.subsystems[name]
        out.append(f"{name}: {sub.score}/5 ({sub.passed}/{sub.total})")
        for check in sub.checks:
            out.append(f"  {'PASS' if check.passed else 'FAIL'} {check.message}")
        out.append("")
    return "\n".join(out)


def escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


_HTML_STYLE = """
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       margin: 32px; color: #172026; background: #f7f8fa; }
main { max-width: 960px; margin: 0 auto; }
header { margin-bottom: 24px; }
h1 { margin: 0 0 8px; font-size: 32px; }
.summary { display: flex; gap: 16px; flex-wrap: wrap; margin: 20px 0; }
.metric { background: white; border: 1px solid #d9dee5; border-radius: 8px;
          padding: 16px 18px; min-width: 180px; }
.metric strong { display: block; font-size: 28px; margin-top: 4px; }
section { background: white; border: 1px solid #d9dee5; border-radius: 8px;
          margin: 14px 0; padding: 16px 18px; }
h2 { margin: 0 0 10px; font-size: 20px; display: flex; justify-content: space-between; }
ul { margin: 0; padding-left: 20px; }
li { margin: 6px 0; }
.pass { color: #126c43; }
.fail { color: #a23020; }
.extras { margin-top: 28px; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #e7eaee; }
"""


def html_report(result: ScoreResult, title: str, extras_html: str = "") -> str:
    sections = []
    for name in SUBSYSTEMS:
        sub = result.subsystems[name]
        items = []
        for check in sub.checks:
            cls = "pass" if check.passed else "fail"
            label = "PASS" if check.passed else "FAIL"
            items.append(
                f'<li class="{cls}">{label} {escape_html(check.message)}</li>'
            )
        sections.append(
            f'<section><h2>{escape_html(name)} <span>{sub.score}/5</span></h2>'
            f'<ul>{"".join(items)}</ul></section>'
        )

    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{escape_html(title)}</title><style>{_HTML_STYLE}</style></head>'
        f'<body><main><header><h1>{escape_html(title)}</h1>'
        f'<p>Five-subsystem harness validation report.</p>'
        f'<div class="summary">'
        f'<div class="metric">Overall<strong>{result.overall}/100</strong></div>'
        f'<div class="metric">Bottleneck<strong>{escape_html(result.bottleneck)}</strong></div>'
        f"</div></header>{''.join(sections)}{extras_html}</main></body></html>"
    )
