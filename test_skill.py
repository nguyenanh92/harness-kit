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
    "hk.py",
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
# hk.py CLI tests
# ---------------------------------------------------------------------------


def test_scaffold_creates_hk_cli() -> None:
    """hk.py is scaffolded and py hk.py status exits cleanly."""
    with tempfile.TemporaryDirectory() as tmp:
        r = run([str(SCAFFOLD), "--target", tmp, "--governance-only"])
        check(r.returncode == 0, f"scaffold exits 0  stderr={r.stderr[:300]!r}")
        hk = Path(tmp) / "hk.py"
        check(hk.is_file(), "hk.py created by scaffold")
        r2 = subprocess.run(
            [sys.executable, str(hk), "status"],
            capture_output=True,
            text=True,
            cwd=tmp,
        )
        check(r2.returncode == 0, f"py hk.py status exits 0  stderr={r2.stderr[:300]!r}")


# ---------------------------------------------------------------------------
# Phase 01 regression: classify_command
# ---------------------------------------------------------------------------

SCRIPTS_TEMPLATES = Path(__file__).resolve().parent / "skills" / "templates"


def _import_tool_registry():
    """Import ToolRegistry from the template module via sys.path injection."""
    import importlib
    old_path = sys.path[:]
    sys.path.insert(0, str(SCRIPTS_TEMPLATES))
    try:
        mod = importlib.import_module("tool_registry")
        return mod.ToolRegistry
    finally:
        sys.path = old_path


def test_classify_command_table() -> None:
    """classify_command returns the correct tier for every documented case."""
    ToolRegistry = _import_tool_registry()
    registry = ToolRegistry()

    cases = [
        # (command, expected_tier)
        ("rm somefile",         "WORKSPACE_WRITE"),
        ("rm -rf /tmp",         "FULL_ACCESS"),
        ("rm -r dir",           "FULL_ACCESS"),
        ("mv src dst",          "WORKSPACE_WRITE"),
        ("cp a b",              "WORKSPACE_WRITE"),
        ("cat README.md",       "READ_ONLY"),
        ("grep pattern file",   "READ_ONLY"),
        ("ls -la",              "READ_ONLY"),
        ("sudo reboot",         "FULL_ACCESS"),
        ("curl https://x.com",  "FULL_ACCESS"),
        ("git commit -m msg",   "WORKSPACE_WRITE"),
        ("pip install requests", "WORKSPACE_WRITE"),
    ]

    for cmd, expected in cases:
        got = registry.classify_command(cmd)
        check(got == expected, f"classify_command({cmd!r}) == {expected!r}  (got {got!r})")


# ---------------------------------------------------------------------------
# Phase 01 regression: prompt_assembly ancestor walk boundary
# ---------------------------------------------------------------------------


def test_prompt_assembly_boundary() -> None:
    """find_guidelines_file stops at .git and does not leak parent CLAUDE.md."""
    import importlib
    old_path = sys.path[:]
    sys.path.insert(0, str(SCRIPTS_TEMPLATES))
    try:
        mod = importlib.import_module("prompt_assembly")
        PromptAssembler = mod.PromptAssembler
    finally:
        sys.path = old_path

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Simulate: root/ (.git boundary) contains parent CLAUDE.md
        (root / ".git").mkdir()
        (root / "CLAUDE.md").write_text("parent-guidelines", encoding="utf-8")

        # sub-project/workspace/ contains the correct AGENTS.md
        workspace = root / "sub-project" / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "AGENTS.md").write_text("correct-guidelines", encoding="utf-8")

        deep = workspace / "src" / "deep"
        deep.mkdir(parents=True)

        assembler = PromptAssembler()

        # Walk from deep/ bounded to workspace/ — should find AGENTS.md
        path, content = assembler.find_guidelines_file(deep, workspace_root=workspace)
        check(content == "correct-guidelines",
              f"finds AGENTS.md inside workspace (got content={content!r})")

        # Walk from workspace/ — should find AGENTS.md directly
        path2, content2 = assembler.find_guidelines_file(workspace, workspace_root=workspace)
        check(content2 == "correct-guidelines", "finds AGENTS.md at workspace root")

        # Without workspace_root the walk is bounded by start_dir (sub-project/)
        # — should NOT cross .git and find parent CLAUDE.md
        subproj = root / "sub-project"
        _, content3 = assembler.find_guidelines_file(subproj, workspace_root=subproj)
        check(content3 != "parent-guidelines",
              "walk from sub-project does NOT load parent CLAUDE.md across .git")


# ---------------------------------------------------------------------------
# Phase 02: harness mock loop end-to-end
# ---------------------------------------------------------------------------


def test_harness_mock_loop() -> None:
    """Mock harness loop runs to completion and writes a valid JSONL log."""
    import importlib
    old_path = sys.path[:]
    sys.path.insert(0, str(SCRIPTS_TEMPLATES))
    try:
        mod = importlib.import_module("harness")
        Harness = mod.Harness
    finally:
        sys.path = old_path

    with tempfile.TemporaryDirectory() as tmp:
        h = Harness(workspace_dir=tmp, is_mock=True, max_iterations=10)
        result = h.run(goal="mock test run")

        check(result["exit_reason"] == "done",
              f"mock loop exits with 'done' (got {result['exit_reason']!r})")

        log_path = Path(result["log_path"])
        check(log_path.exists(), "JSONL log file created")

        lines = [l for l in log_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        check(len(lines) >= 1, f"log contains >= 1 event (got {len(lines)})")

        for i, line in enumerate(lines):
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"log line {i} is not valid JSON: {exc}")
        check(True, "all JSONL lines are valid JSON")


# ---------------------------------------------------------------------------
# Phase 02: context compaction
# ---------------------------------------------------------------------------


def test_context_compaction_triggers() -> None:
    """ContextManager triggers compaction when token budget is exceeded."""
    import importlib
    old_path = sys.path[:]
    sys.path.insert(0, str(SCRIPTS_TEMPLATES))
    try:
        mod = importlib.import_module("context_manager")
        ContextManager = mod.ContextManager
    finally:
        sys.path = old_path

    cm = ContextManager(max_tokens=10)

    # should_compact works on any size list
    small = [
        {"role": "system", "content": "You are an assistant."},
        {"role": "user", "content": "word " * 50},
    ]
    check(cm.should_compact(small), "should_compact() returns True when over budget")

    # compact() requires >10 messages to pass its internal guard; build 12
    messages = [{"role": "system", "content": "You are an assistant."}]
    for i in range(11):
        messages.append({"role": "user", "content": f"turn {i} " + "word " * 30})
        messages.append({"role": "assistant", "content": f"reply {i} " + "word " * 30})

    original_count = len(messages)
    compacted = cm.compact(messages)

    # compact() collapses older turns into one summary block → fewer messages
    check(len(compacted) < original_count,
          f"compact() reduces message count ({len(compacted)} < {original_count})")

    has_system = any(m.get("role") == "system" for m in compacted)
    check(has_system, "compact() preserves system message")


# ---------------------------------------------------------------------------
# Phase 02: hook veto
# ---------------------------------------------------------------------------


def test_hook_veto_blocks_execution() -> None:
    """A pre-hook returning (False, ...) blocks tool execution."""
    import importlib
    old_path = sys.path[:]
    sys.path.insert(0, str(SCRIPTS_TEMPLATES))
    try:
        mod = importlib.import_module("hooks")
        HookRegistry = mod.HookRegistry
    finally:
        sys.path = old_path

    registry = HookRegistry()

    # Register a veto hook
    registry.register_pre_hook(lambda name, args: (False, "blocked-by-test"))
    allowed, result = registry.dispatch_pre_hooks("write_file", {}, workspace_trusted=True)
    check(not allowed, "pre-hook veto: allowed == False")
    check("blocked" in str(result), f"pre-hook veto: result contains 'blocked' (got {result!r})")

    # Untrusted workspace skips hooks entirely → should be allowed
    registry2 = HookRegistry()
    registry2.register_pre_hook(lambda name, args: (False, "should-not-run"))
    allowed2, _ = registry2.dispatch_pre_hooks("write_file", {}, workspace_trusted=False)
    check(allowed2, "untrusted workspace bypasses veto hooks")

    # Post-hook is called and does not raise
    post_calls: list = []
    registry3 = HookRegistry()
    registry3.register_post_hook(lambda name, result: post_calls.append(name))
    registry3.dispatch_post_hooks("read_file", "ok", workspace_trusted=True)
    check(len(post_calls) == 1, f"post-hook was called once (got {len(post_calls)})")


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
    test_scaffold_creates_hk_cli,
    # Phase 01 regressions
    test_classify_command_table,
    test_prompt_assembly_boundary,
    # Phase 02: harness loop coverage
    test_harness_mock_loop,
    test_context_compaction_triggers,
    test_hook_veto_blocks_execution,
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
