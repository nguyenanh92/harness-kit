"""Score a harnessed project across five subsystems.

Usage:
    python validate_harness.py --target /path/to/project
    python validate_harness.py --target . --html report.html
    python validate_harness.py --json --min-score 80
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.harness_utils import (  # noqa: E402
    format_text_report,
    html_report,
    score_harness,
)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score a harnessed project across five subsystems.",
    )
    parser.add_argument(
        "--target", default=".",
        help="Project root to audit (default: '.').",
    )
    parser.add_argument(
        "--harness-dir", default=None,
        help="Where the Python harness modules live (default: '<target>/harness').",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--html", default=None, help="Write a self-contained HTML report.")
    parser.add_argument("--min-score", type=int, default=70,
                        help="Exit non-zero if overall < this (default: 70).")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.target).resolve()
    harness_dir = Path(args.harness_dir).resolve() if args.harness_dir else None

    result = score_harness(root, harness_dir=harness_dir)

    if args.html:
        out = Path(args.html).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            html_report(result, f"Harness Assessment: {root.name}"),
            encoding="utf-8",
        )
        print(f"HTML report: {out}")

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(format_text_report(result, root))

    return 0 if result.overall >= args.min_score else 1


if __name__ == "__main__":
    raise SystemExit(main())
