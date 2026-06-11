"""Render a self-contained HTML assessment for a harness.

Usage:
    python render_assessment_html.py --target . --output report.html
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.harness_utils import html_report, score_harness  # noqa: E402


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a self-contained HTML harness assessment.",
    )
    parser.add_argument("--target", default=".",
                        help="Project root to audit (default: '.').")
    parser.add_argument("--output", default=None,
                        help="HTML output path (default: <target>/harness-assessment.html).")
    parser.add_argument("--harness-dir", default=None,
                        help="Where the Python harness modules live.")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.target).resolve()
    out = Path(args.output).resolve() if args.output else root / "harness-assessment.html"
    harness_dir = Path(args.harness_dir).resolve() if args.harness_dir else None

    result = score_harness(root, harness_dir=harness_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        html_report(result, f"Harness Assessment: {root.name}"),
        encoding="utf-8",
    )
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
