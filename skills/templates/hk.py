#!/usr/bin/env python3
"""hk — harness-kit workflow CLI.

Works from any IDE, agent, or shell — no special plugins required.
Standard library only. Python 3.8+.

Commands
--------
  feature <name> [--desc TEXT] [--deps F-001,F-002]
      Add a feature to feature_list.json.

  start [FEATURE_ID]
      Set a feature as in_progress and make it the active feature.

  status
      Show the active feature, queue summary, and next recommended step.

  done [FEATURE_ID]
      Run the verification script, then mark the feature done.

  audit [--html PATH]
      Score the harness (0-100). Built-in — no extra files required.

  handoff
      Auto-generate session-handoff.md from active feature, git log, and
      progress.md. Run at the end of each session before closing.

Usage from any directory in the project
-----------------------------------------
  py hk.py feature "Notification Settings"
  py hk.py start F-014
  py hk.py status
  py hk.py done
  py hk.py audit --html report.html
  py hk.py handoff       # generate session-handoff.md at end of session
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Ensure UTF-8 output on Windows (cp1252 default breaks arrow/checkmark chars).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# =========================================================================== #
# Inline scorer (ported from harness_utils.py — stdlib only, no imports)
# =========================================================================== #

_SUBSYSTEMS: Tuple[str, ...] = (
    "instructions", "state", "verification", "scope", "lifecycle",
)

_CODE_MODULES: Tuple[str, ...] = (
    "harness.py", "context_manager.py", "tool_registry.py",
    "persistence.py", "hooks.py", "subagent.py", "prompt_assembly.py",
)

_GOVERNANCE_CANDIDATES: Tuple[str, ...] = (
    "AGENTS.md", "CLAUDE.md",
    "feature_list.json", "feature-list.json",
    "progress.md", "session-handoff.md",
    "init.sh", "init.ps1", "init.bat", "init.cmd",
)

_FEATURE_ID_RE = re.compile(r"^F-\d+$|^feat-\d+$", re.IGNORECASE)
_ALLOWED_STATUS = {"pending", "in_progress", "blocked", "done", "not-started", "not_started"}


@dataclass
class _Check:
    passed: bool
    message: str


@dataclass
class _SubsystemResult:
    name: str
    score: int
    passed: int
    total: int
    checks: List[_Check] = field(default_factory=list)


@dataclass
class _ScoreResult:
    overall: int
    bottleneck: str
    subsystems: Dict[str, _SubsystemResult]


def _compile_needle(needle: str) -> re.Pattern:
    escaped = re.escape(needle)
    left  = r"\b" if needle[:1].isalnum() or needle[:1] == "_" else ""
    right = r"\b" if needle[-1:].isalnum() or needle[-1:] == "_" else ""
    return re.compile(left + escaped + right, re.IGNORECASE)


def _text_has(text: str, needles: Iterable[str]) -> bool:
    if not text:
        return False
    for needle in needles:
        if _compile_needle(needle).search(text):
            return True
    return False


def _has_file(files: Dict[str, str], names: Iterable[str]) -> bool:
    return any(name in files for name in names)


def _validate_feature_list(raw: str) -> Tuple[bool, List[str]]:
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


def _load_governance(root: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for name in _GOVERNANCE_CANDIDATES:
        path = root / name
        if path.is_file():
            try:
                out[name] = path.read_text(encoding="utf-8")
            except OSError:
                continue
    return out


def _list_code_modules(harness_dir: Path) -> Dict[str, bool]:
    return {name: (harness_dir / name).is_file() for name in _CODE_MODULES}


def _score_harness(root: Path, harness_dir: Optional[Path] = None) -> _ScoreResult:
    governance = _load_governance(root)
    if harness_dir is None:
        candidate = root / "harness"
        harness_dir = candidate if candidate.is_dir() else root
    code = _list_code_modules(harness_dir)

    agents_text  = governance.get("AGENTS.md", "") or governance.get("CLAUDE.md", "")
    feature_text = governance.get("feature_list.json", "") or governance.get("feature-list.json", "")
    progress     = governance.get("progress.md", "")
    handoff      = governance.get("session-handoff.md", "")
    init_text    = ""
    for name in ("init.sh", "init.ps1", "init.bat", "init.cmd"):
        if name in governance:
            init_text = governance[name]
            break
    all_text = "\n\n".join(governance.values())
    feature_valid, _ = _validate_feature_list(feature_text) if feature_text else (False, [])

    instructions = [
        _Check(_has_file(governance, ["AGENTS.md", "CLAUDE.md"]),
               "Agent instruction file exists"),
        _Check(_text_has(agents_text, ["Startup Workflow", "Before writing code"]),
               "Startup workflow documented"),
        _Check(_text_has(agents_text, ["Definition of Done", "done only when"]),
               "Definition of Done documented"),
        _Check(_text_has(agents_text, ["Verification Commands", "./init.sh", "./init.ps1", "verify"]),
               "Verification commands discoverable"),
        _Check(_text_has(agents_text, ["feature_list.json", "progress.md", "session-handoff.md"]),
               "State artifacts routed from instructions"),
    ]

    state = [
        _Check(_has_file(governance, ["feature_list.json", "feature-list.json"]),
               "Feature tracker exists"),
        _Check(feature_valid, "Feature tracker is valid"),
        _Check(_has_file(governance, ["progress.md"]), "Progress log exists"),
        _Check(_text_has(progress, ["Current State", "Current Objective", "Next Step", "What I Did"]),
               "Progress log supports restart"),
        _Check(_text_has(handoff or progress, ["Blockers", "Files", "Next Session"]),
               "Handoff captures blockers, files, and next step"),
    ]

    verification = [
        _Check(_has_file(governance, ["init.sh", "init.ps1", "init.bat", "init.cmd"]),
               "Verification entrypoint exists"),
        _Check(_text_has(init_text, ["set -e", "$ErrorActionPreference", "errorlevel", "exit /b"]),
               "Verification fails fast"),
        _Check(_text_has(init_text + agents_text,
                         ["pytest", "unittest", "vitest", "cargo test", "go test", "dotnet test"]),
               "Test command documented"),
        _Check(_text_has(init_text + agents_text,
                         ["py_compile", "compileall", "build", "type", "lint", "compile"]),
               "Static / build check documented"),
        _Check(_text_has(all_text, ["Evidence", "Verification Evidence", "command and output"]),
               "Verification evidence is recorded"),
    ]

    scope = [
        _Check(_text_has(agents_text, ["One feature at a time", "one-feature-at-a-time"]),
               "One-feature-at-a-time rule exists"),
        _Check(_text_has(feature_text, ["dependencies"]),
               "Feature dependencies are tracked"),
        _Check(_text_has(agents_text + feature_text, ["status"]),
               "Feature status is explicit"),
        _Check(_text_has(agents_text, ["Stay in scope", "Stay in Scope", "scope"]),
               "Scope boundary documented"),
        _Check(_text_has(agents_text, ["Definition of Done"]),
               "Completion gate limits scope closure"),
    ]

    is_governance_only = bool(governance) and not (root / "harness").is_dir()
    lifecycle = [
        _Check(_has_file(governance, ["init.sh", "init.ps1", "init.bat", "init.cmd"]),
               "Startup script exists"),
        _Check(_text_has(agents_text, ["End of Session", "Before ending"]),
               "End-of-session procedure exists"),
        _Check(_has_file(governance, ["session-handoff.md"]),
               "Session handoff template exists"),
        _Check(_text_has(progress + handoff,
                         ["Last Updated", "Current Objective", "Recommended Next Step"]),
               "Session restart markers exist"),
        _Check(any(code.values()) or is_governance_only,
               "Harness code modules scaffolded"),
    ]

    raw: Dict[str, List[_Check]] = {
        "instructions": instructions,
        "state": state,
        "verification": verification,
        "scope": scope,
        "lifecycle": lifecycle,
    }
    subsystems: Dict[str, _SubsystemResult] = {}
    total = 0
    for name in _SUBSYSTEMS:
        checks = raw[name]
        passed = sum(1 for c in checks if c.passed)
        score = round(passed / len(checks) * 5)
        subsystems[name] = _SubsystemResult(
            name=name, score=score, passed=passed,
            total=len(checks), checks=checks,
        )
        total += score

    overall = round(total / (len(_SUBSYSTEMS) * 5) * 100)
    bottleneck = min(_SUBSYSTEMS, key=lambda n: (subsystems[n].score, _SUBSYSTEMS.index(n)))
    return _ScoreResult(overall=overall, bottleneck=bottleneck, subsystems=subsystems)


def _format_text_report(result: _ScoreResult, root: Path) -> str:
    lines = [
        f"Harness score for {root}",
        f"Overall: {result.overall}/100  (bottleneck: {result.bottleneck})",
        "",
    ]
    for name in _SUBSYSTEMS:
        sub = result.subsystems[name]
        lines.append(f"{name}: {sub.score}/5 ({sub.passed}/{sub.total})")
        for check in sub.checks:
            lines.append(f"  {'PASS' if check.passed else 'FAIL'} {check.message}")
        lines.append("")
    return "\n".join(lines)


def _escape_html(v: str) -> str:
    return v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


_HTML_STYLE = """
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
     margin:32px;color:#172026;background:#f7f8fa;}
main{max-width:900px;margin:0 auto;}
h1{margin:0 0 8px;font-size:28px;}
.summary{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;}
.metric{background:white;border:1px solid #d9dee5;border-radius:8px;
        padding:14px 16px;min-width:160px;}
.metric strong{display:block;font-size:24px;margin-top:4px;}
section{background:white;border:1px solid #d9dee5;border-radius:8px;
        margin:12px 0;padding:14px 16px;}
h2{margin:0 0 8px;font-size:18px;display:flex;justify-content:space-between;}
ul{margin:0;padding-left:18px;}
li{margin:5px 0;}
.pass{color:#126c43;}.fail{color:#a23020;}
"""


def _html_report(result: _ScoreResult, title: str) -> str:
    sections = []
    for name in _SUBSYSTEMS:
        sub = result.subsystems[name]
        items = "".join(
            f'<li class="{"pass" if c.passed else "fail"}">'
            f'{"PASS" if c.passed else "FAIL"} {_escape_html(c.message)}</li>'
            for c in sub.checks
        )
        sections.append(
            f'<section><h2>{_escape_html(name)} <span>{sub.score}/5</span></h2>'
            f'<ul>{items}</ul></section>'
        )
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<title>{_escape_html(title)}</title><style>{_HTML_STYLE}</style></head>'
        f'<body><main><h1>{_escape_html(title)}</h1>'
        f'<div class="summary">'
        f'<div class="metric">Overall<strong>{result.overall}/100</strong></div>'
        f'<div class="metric">Bottleneck<strong>{_escape_html(result.bottleneck)}</strong></div>'
        f'</div>{"".join(sections)}</main></body></html>'
    )


# =========================================================================== #
# Root resolution
# =========================================================================== #

def find_root(start: Path) -> Optional[Path]:
    """Walk up from start looking for feature_list.json."""
    for p in [start, *start.parents]:
        if (p / "feature_list.json").is_file():
            return p
    return None


# =========================================================================== #
# feature_list.json helpers
# =========================================================================== #

def load_fl(root: Path) -> Dict[str, Any]:
    return json.loads((root / "feature_list.json").read_text(encoding="utf-8"))


def save_fl(root: Path, data: Dict[str, Any]) -> None:
    path = root / "feature_list.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def next_id(features: List[Dict]) -> str:
    nums = [int(m.group(1)) for f in features
            if (m := re.match(r"F-(\d+)$", f.get("id", ""), re.IGNORECASE))]
    return f"F-{(max(nums) + 1) if nums else 1:03d}"


def get_feature(features: List[Dict], fid: str) -> Optional[Dict]:
    return next((f for f in features if f.get("id") == fid), None)


def _agent_instruction_hint(root: Path) -> str:
    for name in ("CLAUDE.md", "AGENTS.md", ".cursorrules"):
        if (root / name).is_file():
            return name
    return "CLAUDE.md"


_STARTER_NAMES = {"Bootstrap harness", "Wire verification"}


def _is_starter_list(features: List[Dict]) -> bool:
    """True when the feature list still contains only the scaffold placeholder entries."""
    return bool(features) and all(f.get("name") in _STARTER_NAMES for f in features)


# =========================================================================== #
# Commands
# =========================================================================== #

def cmd_feature(args: argparse.Namespace, root: Path) -> int:
    data = load_fl(root)
    features: List[Dict] = data.setdefault("features", [])

    fid = next_id(features)
    name = args.name
    desc = getattr(args, "desc", None) or name
    raw_deps = getattr(args, "deps", None) or ""
    deps = [d.strip() for d in raw_deps.split(",") if d.strip()]

    has_active = any(f.get("status") == "in_progress" for f in features)
    status = "pending" if has_active else "in_progress"

    feature: Dict[str, Any] = {
        "id": fid,
        "name": name,
        "description": desc,
        "status": status,
        "dependencies": deps,
        "evidence": "",
    }
    features.append(feature)
    if status == "in_progress":
        data["active_feature"] = fid

    save_fl(root, data)
    print(f"+ {fid}: {name}  [{status}]")
    if status == "pending":
        print(f"  Queued behind {data.get('active_feature', '?')} (still in_progress).")
        print(f"  Run: py hk.py start {fid}  — to promote it now.")
    return 0


def cmd_start(args: argparse.Namespace, root: Path) -> int:
    data = load_fl(root)
    features: List[Dict] = data.get("features", [])

    fid = getattr(args, "feature_id", None) or data.get("active_feature")
    if not fid:
        print("Error: specify a feature ID or set active_feature first.", file=sys.stderr)
        return 1

    feature = get_feature(features, fid)
    if not feature:
        print(f"Error: {fid} not found in feature_list.json.", file=sys.stderr)
        return 1

    if feature.get("status") == "done":
        print(f"Warning: {fid} is already done. Use --force to restart.", file=sys.stderr)
        if not getattr(args, "force", False):
            return 1

    for f in features:
        if f.get("status") == "in_progress" and f.get("id") != fid:
            f["status"] = "pending"
            print(f"  Paused {f['id']} → pending")

    feature["status"] = "in_progress"
    data["active_feature"] = fid
    save_fl(root, data)
    print(f"[→] Active: {fid} — {feature['name']}")
    print()
    print("  Open your AI agent in this directory and say:")
    print('  > "Read AGENTS.md and implement the active feature in feature_list.json."')
    print()
    print("  Quick start:  claude  (Claude Code)  |  cursor .  (Cursor)  |  codex  (Codex)")
    return 0


def cmd_status(args: argparse.Namespace, root: Path) -> int:
    data = load_fl(root)
    features: List[Dict] = data.get("features", [])
    active_id = data.get("active_feature")

    active = get_feature(features, active_id) if active_id else None
    if active:
        print(f"Active  [{active['status']}] {active['id']} — {active['name']}")
        if active.get("description") and active["description"] != active["name"]:
            print(f"        {active['description']}")
        deps = active.get("dependencies", [])
        if deps:
            print(f"        deps: {', '.join(deps)}")
    else:
        print("No active feature.")
        print("  Start one:  py hk.py start F-001")

    by_status: Dict[str, List[str]] = {}
    for f in features:
        s = f.get("status", "?")
        by_status.setdefault(s, []).append(f["id"])

    counts = "  ·  ".join(f"{len(v)} {k}" for k, v in sorted(by_status.items()))
    print(f"\nQueue   {counts}  ·  {len(features)} total")

    pending = [f for f in features if f.get("status") == "pending"]
    if pending:
        print(f"Next    {pending[0]['id']} — {pending[0]['name']}")

    # Hint when still on scaffold placeholder features
    if _is_starter_list(features):
        print("\nTip     These are starter features. Replace with your own:")
        print("          py hk.py feature \"Your first task\" --desc \"What you want to build\"")

    # Surface recommended next step from progress.md
    progress_md = root / "progress.md"
    if progress_md.is_file():
        text = progress_md.read_text(encoding="utf-8")
        m = re.search(r"##\s*Recommended Next Step\n+(.*?)(?=\n##|\Z)", text, re.DOTALL)
        if m:
            tip = m.group(1).strip().splitlines()[0][:160]
            print(f"\nTip     {tip}")
    return 0


def cmd_done(args: argparse.Namespace, root: Path) -> int:
    data = load_fl(root)
    features: List[Dict] = data.get("features", [])

    fid = getattr(args, "feature_id", None) or data.get("active_feature")
    if not fid:
        print("Error: no feature ID given and no active_feature set.", file=sys.stderr)
        return 1

    feature = get_feature(features, fid)
    if not feature:
        print(f"Error: {fid} not found.", file=sys.stderr)
        return 1

    init_ps1 = root / "init.ps1"
    init_sh  = root / "init.sh"

    if sys.platform == "win32" and init_ps1.is_file():
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(init_ps1)]
    elif init_sh.is_file():
        cmd = ["bash", str(init_sh)]
    else:
        print("Error: no init.sh or init.ps1 found.", file=sys.stderr)
        return 1

    print("Verifying workspace …")
    result = subprocess.run(cmd, cwd=root)
    if result.returncode != 0:
        print("\nVerification FAILED — fix errors before marking done.")
        return 1

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    feature["status"] = "done"
    feature["evidence"] = f"Verified {timestamp}: init script passed"
    save_fl(root, data)

    progress_md = root / "progress.md"
    if progress_md.is_file():
        text = progress_md.read_text(encoding="utf-8")
        text = re.sub(r"\*\*Last Updated:\*\*[^\n]*", f"**Last Updated:** {timestamp}", text)
        progress_md.write_text(text, encoding="utf-8")

    print(f"\n✓ {fid} done — evidence recorded, progress.md updated.")

    next_p = next((f for f in features if f.get("status") == "pending"), None)
    if next_p:
        print(f"  Next up: {next_p['id']} — {next_p['name']}")
        print(f"  Run: py hk.py start {next_p['id']}")
    return 0


def cmd_audit(args: argparse.Namespace, root: Path) -> int:
    """Score the harness using the built-in inline scorer."""
    result = _score_harness(root)
    html_out = getattr(args, "html", None)
    if html_out:
        out = Path(html_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_html_report(result, f"Harness: {root.name}"), encoding="utf-8")
        print(f"HTML report: {out}")
    print(_format_text_report(result, root))
    return 0 if result.overall >= 70 else 1


def cmd_handoff(args: argparse.Namespace, root: Path) -> int:
    """Generate session-handoff.md from active feature, git log, and progress.md."""
    data = load_fl(root)
    features: List[Dict] = data.get("features", [])
    active_id = data.get("active_feature")
    active = get_feature(features, active_id) if active_id else None
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    def _git(*cmd: str) -> str:
        try:
            r = subprocess.run(["git", *cmd], capture_output=True, text=True,
                               cwd=root, timeout=5)
            return r.stdout.strip() if r.returncode == 0 else ""
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return ""

    branch     = _git("rev-parse", "--abbrev-ref", "HEAD")
    recent_log = _git("log", "--oneline", "-5")
    diff_stat  = _git("diff", "--stat", "HEAD~1") or _git("status", "--short")

    first_hash = ""
    if recent_log:
        m = re.match(r"([0-9a-f]{6,})", recent_log)
        if m:
            first_hash = m.group(1)
    commit_ref = f"{branch} @ {first_hash}" if (branch and first_hash) else branch or "(no git)"

    next_step = ""
    progress_file = root / "progress.md"
    if progress_file.is_file():
        text = progress_file.read_text(encoding="utf-8")
        m = re.search(r"##\s*Recommended Next Step\s*\n+(.*?)(?=\n##|\Z)", text, re.DOTALL)
        if m:
            next_step = m.group(1).strip()

    done_features = [f for f in features if f.get("status") == "done"]
    agent_file = _agent_instruction_hint(root)

    out: List[str] = [
        "# Session Handoff",
        "",
        "## Current Objective",
        "",
        f"- Goal: {active['name'] if active else 'N/A'}",
        f"- Current status: {active.get('status', '') if active else 'N/A'}",
        f"- Branch / commit: {commit_ref}",
        "",
        "## Completed This Session",
        "",
    ]
    if done_features:
        for f in done_features[-3:]:
            out.append(f"- [x] {f['id']} — {f['name']}")
    else:
        out.append("- [ ] (none yet)")

    out += [
        "",
        "## Verification Evidence",
        "",
        "| Check | Command | Result | Notes |",
        "|---|---|---|---|",
        "|  |  |  |  |",
        "",
        "## Files Changed",
        "",
    ]
    if diff_stat:
        for line in diff_stat.splitlines()[:12]:
            out.append(f"- {line}")
    else:
        out.append("- (run `git status` to see changes)")

    out += ["", "## Recent Commits", ""]
    if recent_log:
        for line in recent_log.splitlines():
            out.append(f"- {line}")
    else:
        out.append("- (no git history)")

    out += [
        "",
        "## Decisions Made",
        "",
        "- ",
        "",
        "## Blockers / Risks",
        "",
        "- ",
        "",
        "## Next Session Startup",
        "",
        f"1. Read `{agent_file}`.",
        "2. Read `feature_list.json` and `progress.md`.",
        "3. Review this handoff.",
        "4. Run `./init.sh` or the documented verification command before editing.",
        "",
        "## Recommended Next Step",
        "",
    ]
    if next_step:
        for line in next_step.splitlines()[:3]:
            if line.strip():
                out.append(f"- {line.lstrip('-• ').strip()}")
    elif active:
        out.append(f"- Continue {active['id']}: {active.get('description', active['name'])}")
    else:
        out.append("- ")

    (root / "session-handoff.md").write_text("\n".join(out) + "\n", encoding="utf-8")

    print(f"✓ session-handoff.md written  ({timestamp})")
    if active:
        print(f"  Active : {active['id']} — {active['name']}")
    if branch:
        print(f"  Branch : {commit_ref}")
    return 0


# =========================================================================== #
# Entry point
# =========================================================================== #

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hk",
        description="harness-kit CLI — any IDE, agent, or shell.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--target", default=".",
        help="Project root (default: walk up from cwd to find feature_list.json).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # feature
    p_feat = sub.add_parser("feature", help="Add a feature to feature_list.json")
    p_feat.add_argument("name", help="Short feature name")
    p_feat.add_argument("--desc", help="Longer description (defaults to name)")
    p_feat.add_argument("--deps", metavar="IDs", help="Comma-separated dependency IDs")

    # start
    p_start = sub.add_parser("start", help="Set a feature as in_progress")
    p_start.add_argument("feature_id", nargs="?", help="Feature ID (default: active_feature)")
    p_start.add_argument("--force", action="store_true", help="Restart a done feature")

    # status
    sub.add_parser("status", help="Show active feature, queue, and next step")

    # done
    p_done = sub.add_parser("done", help="Verify workspace, then mark feature done")
    p_done.add_argument("feature_id", nargs="?", help="Feature ID (default: active_feature)")

    # audit
    p_audit = sub.add_parser("audit", help="Score the harness (0-100)")
    p_audit.add_argument("--html", metavar="PATH", help="Write HTML report to PATH")

    # handoff
    sub.add_parser("handoff", help="Generate session-handoff.md from current project state")

    args = parser.parse_args(argv)

    given = Path(args.target).resolve()
    root = find_root(given) or given

    dispatch = {
        "feature": cmd_feature,
        "start":   cmd_start,
        "status":  cmd_status,
        "done":    cmd_done,
        "audit":   cmd_audit,
        "handoff": cmd_handoff,
    }
    return dispatch[args.command](args, root)


if __name__ == "__main__":
    raise SystemExit(main())
