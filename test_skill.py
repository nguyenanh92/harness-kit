"""Regression tests for harness-kit skill scripts.

Run:
    python test_skill.py

Standard library only. Python 3.8+. Works on Windows, macOS, Linux.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent / "skills" / "scripts"
SCAFFOLD = SCRIPTS / "scaffold_harness.py"
VALIDATE = SCRIPTS / "validate_harness.py"

GOVERNANCE_FILES = (
    "AGENTS.md",
    "feature_list.json",
    "feature-list.schema.json",
    "progress.md",
    "session-handoff.md",
)


def run(cmd: list) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable] + cmd,
        capture_output=True,
        text=True,
    )


def check(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"  PASS  {label}")


# ---------------------------------------------------------------------------
# scaffold_harness.py tests
# ---------------------------------------------------------------------------


def test_scaffold_governance_only() -> None:
    """--governance-only creates governance files and no harness/ directory."""
    with tempfile.TemporaryDirectory() as tmp:
        r = run([str(SCAFFOLD), "--target", tmp, "--governance-only"])
        check(r.returncode == 0, f"scaffold exits 0  stderr={r.stderr[:300]!r}")
        for fname in GOVERNANCE_FILES:
            check((Path(tmp) / fname).is_file(), f"{fname} created")
        check(not (Path(tmp) / "harness").exists(), "harness/ NOT created in governance-only mode")


def test_scaffold_full_creates_code_modules() -> None:
    """Default mode also emits harness/ Python modules."""
    with tempfile.TemporaryDirectory() as tmp:
        r = run([str(SCAFFOLD), "--target", tmp])
        check(r.returncode == 0, f"scaffold (full) exits 0  stderr={r.stderr[:300]!r}")
        check((Path(tmp) / "AGENTS.md").is_file(), "AGENTS.md created")
        harness = Path(tmp) / "harness"
        check(harness.is_dir(), "harness/ directory created")
        check((harness / "harness.py").is_file(), "harness/harness.py created")


def test_scaffold_agent_file_claude() -> None:
    """--agent-file CLAUDE.md emits CLAUDE.md instead of AGENTS.md."""
    with tempfile.TemporaryDirectory() as tmp:
        r = run([str(SCAFFOLD), "--target", tmp, "--governance-only", "--agent-file", "CLAUDE.md"])
        check(r.returncode == 0, f"scaffold --agent-file CLAUDE.md exits 0  stderr={r.stderr[:300]!r}")
        check((Path(tmp) / "CLAUDE.md").is_file(), "CLAUDE.md created")
        check(not (Path(tmp) / "AGENTS.md").is_file(), "AGENTS.md NOT created")


def test_scaffold_skip_existing_without_force() -> None:
    """Without --force, existing files are not overwritten."""
    with tempfile.TemporaryDirectory() as tmp:
        run([str(SCAFFOLD), "--target", tmp, "--governance-only"])
        agents = Path(tmp) / "AGENTS.md"
        agents.write_text("sentinel", encoding="utf-8")
        run([str(SCAFFOLD), "--target", tmp, "--governance-only"])
        check(agents.read_text(encoding="utf-8") == "sentinel", "file preserved without --force")


def test_scaffold_force_overwrites() -> None:
    """--force rewrites files that already exist."""
    with tempfile.TemporaryDirectory() as tmp:
        run([str(SCAFFOLD), "--target", tmp, "--governance-only"])
        agents = Path(tmp) / "AGENTS.md"
        original = agents.read_text(encoding="utf-8")
        agents.write_text("corrupted", encoding="utf-8")
        r = run([str(SCAFFOLD), "--target", tmp, "--governance-only", "--force"])
        check(r.returncode == 0, "--force scaffold exits 0")
        check(agents.read_text(encoding="utf-8") == original, "--force restores original content")


# ---------------------------------------------------------------------------
# validate_harness.py tests
# ---------------------------------------------------------------------------


def test_validate_json_output() -> None:
    """validate emits valid JSON with an 'overall' numeric key."""
    with tempfile.TemporaryDirectory() as tmp:
        run([str(SCAFFOLD), "--target", tmp, "--governance-only"])
        r = run([str(VALIDATE), "--target", tmp, "--min-score", "0", "--json"])
        check(r.returncode == 0, f"validate exits 0  stderr={r.stderr[:300]!r}")
        data = json.loads(r.stdout)
        check("overall" in data, "JSON has 'overall' key")
        check(isinstance(data["overall"], (int, float)), "'overall' is numeric")
        check(0 <= data["overall"] <= 100, "score in [0, 100]")


def test_validate_min_score_zero_passes() -> None:
    """validate exits 0 when --min-score 0 on an empty dir."""
    with tempfile.TemporaryDirectory() as tmp:
        r = run([str(VALIDATE), "--target", tmp, "--min-score", "0"])
        check(r.returncode == 0, "exits 0 with --min-score 0 on empty dir")


def test_validate_min_score_100_fails_on_empty() -> None:
    """validate exits non-zero when empty dir scores below 100."""
    with tempfile.TemporaryDirectory() as tmp:
        r = run([str(VALIDATE), "--target", tmp, "--min-score", "100"])
        check(r.returncode != 0, "exits non-zero when empty dir scores < 100")


def test_validate_scaffolded_dir_above_threshold() -> None:
    """A freshly scaffolded dir scores above 50."""
    with tempfile.TemporaryDirectory() as tmp:
        run([str(SCAFFOLD), "--target", tmp, "--governance-only"])
        r = run([str(VALIDATE), "--target", tmp, "--min-score", "0", "--json"])
        data = json.loads(r.stdout)
        check(data["overall"] >= 50, f"scaffolded dir scores >= 50 (got {data['overall']})")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    test_scaffold_governance_only,
    test_scaffold_full_creates_code_modules,
    test_scaffold_agent_file_claude,
    test_scaffold_skip_existing_without_force,
    test_scaffold_force_overwrites,
    test_validate_json_output,
    test_validate_min_score_zero_passes,
    test_validate_min_score_100_fails_on_empty,
    test_validate_scaffolded_dir_above_threshold,
]


def main() -> None:
    failures: list = []

    for t in TESTS:
        print(f"\n{t.__name__}")
        try:
            t()
        except Exception as exc:
            print(f"  FAIL  {exc}")
            failures.append(t.__name__)

    total = len(TESTS)
    print(f"\n{'=' * 52}")
    if failures:
        print(f"FAILED {len(failures)}/{total}")
        for name in failures:
            print(f"  - {name}")
        sys.exit(1)
    else:
        print(f"OK  {total}/{total} passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
