"""Scaffold a zero-dependency Python agent harness into a project.

Governance files (AGENTS.md, feature_list.json, progress.md, ...) land at the
project root; the 9-component Python modules land inside ``<root>/<harness>/``.

Usage:
    python scaffold_harness.py --target . --harness-dir harness
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

# Allow ``python scripts/scaffold_harness.py`` to find the lib next to itself.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.harness_utils import (  # noqa: E402
    CODE_TEMPLATES,
    CopyResult,
    GOVERNANCE_TEMPLATES,
    copy_template,
    detect_project,
    primary_verification_command,
)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a zero-dep Python agent harness.",
    )
    parser.add_argument(
        "--target", default=".",
        help="Project root that receives governance files (default: '.').",
    )
    parser.add_argument(
        "--harness-dir", default="harness",
        help="Subdirectory for the 9-component Python modules (default: 'harness').",
    )
    parser.add_argument(
        "--agent-file", default="AGENTS.md",
        choices=["AGENTS.md", "CLAUDE.md"],
        help="Name to use for the agent instruction file (default: AGENTS.md).",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite files that already exist.",
    )
    parser.add_argument(
        "--governance-only", action="store_true",
        help="Skip the Python code modules; emit governance files only.",
    )
    return parser.parse_args(argv)


def print_result(result: CopyResult) -> None:
    if result.status == "written":
        print(f"  + {result.path}")
    else:
        suffix = f" ({result.reason})" if result.reason else ""
        print(f"  . skipped {result.path}{suffix}")


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.target).resolve()
    harness_dir = (root / args.harness_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)

    info = detect_project(root)
    replacements = {
        "AGENT_FILE_NAME": args.agent_file,
        "HARNESS_DIR": args.harness_dir,
        "PRIMARY_VERIFICATION_COMMAND": primary_verification_command(info),
        "PROJECT_STACK": info.stack,
    }

    print(f"Scaffolding harness into {root}")
    print(f"  detected stack: {info.stack}")
    print(f"  harness dir:    {harness_dir.relative_to(root)}/")
    print(f"  governance:     {root}/  (using {args.agent_file})")
    print()

    print("Governance:")
    for name in GOVERNANCE_TEMPLATES:
        rename_to = args.agent_file if name == "AGENTS.md" else None
        result = copy_template(
            name, root, replacements=replacements,
            force=args.force, rename_to=rename_to,
        )
        print_result(result)

    if not args.governance_only:
        harness_dir.mkdir(parents=True, exist_ok=True)
        # Ship an empty __init__.py so the harness folder is importable.
        init_file = harness_dir / "__init__.py"
        if not init_file.exists() or args.force:
            init_file.write_text("", encoding="utf-8")
        print("\nCode modules:")
        for name in CODE_TEMPLATES:
            result = copy_template(
                name, harness_dir, replacements=replacements, force=args.force
            )
            print_result(result)

    print(
        f"\nDone. Next: edit {args.agent_file}, fill in feature_list.json, "
        f"run ./init.sh (or ./init.ps1) to verify, then start coding."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
