"""Structural benchmark: combine harness score with eval coverage.

Loads evals/evals.json next to the skill, checks how many cases the current
harness state plausibly covers, and emits JSON (+ optional HTML).

Usage:
    python run_benchmark.py --target .
    python run_benchmark.py --target . --html benchmark.html --min-score 80
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.harness_utils import (  # noqa: E402
    SKILL_ROOT,
    SUBSYSTEMS,
    escape_html,
    html_report,
    score_harness,
)


def load_evals(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "cases" in data:
        return data["cases"]
    if isinstance(data, list):
        return data
    return []


def eval_coverage(cases: List[Dict[str, Any]], result) -> Dict[str, Any]:
    """A *structural* coverage proxy: each eval is "covered" if its primary
    subsystem scored at least 3/5. The mapping below is conservative; treat
    the number as a smoke test, not a real benchmark.
    """
    keyword_to_subsystem = [
        (("scaffold", "minimal", "lifecycle", "bootstrap"), "lifecycle"),
        (("validate", "score", "assessment", "audit"), "instructions"),
        (("verification", "verify", "init.sh", "evidence"), "verification"),
        (("memory", "persistence", "jsonl", "replay"), "state"),
        (("session", "handoff", "restart"), "lifecycle"),
        (("tool", "permission", "safety", "shell"), "verification"),
        (("context", "compaction", "budget"), "state"),
        (("multi-agent", "sub-agent", "subagent", "fork"), "scope"),
        (("scope", "feature", "definition of done"), "scope"),
        (("prompt", "assembly", "prefix cache"), "instructions"),
    ]

    covered: List[str] = []
    uncovered: List[str] = []
    for case in cases:
        text = " ".join(
            str(case.get(k, "")) for k in ("name", "prompt", "expected_output")
        ).lower()
        subsystem = None
        for needles, name in keyword_to_subsystem:
            if any(n in text for n in needles):
                subsystem = name
                break
        if subsystem is None:
            uncovered.append(case.get("name", "<unnamed>"))
            continue
        if result.subsystems[subsystem].score >= 3:
            covered.append(case.get("name", "<unnamed>"))
        else:
            uncovered.append(case.get("name", "<unnamed>"))

    if not cases:
        score = 0
    else:
        score = round(len(covered) / len(cases) * 100)
    return {
        "total": len(cases),
        "covered": covered,
        "uncovered": uncovered,
        "score": score,
    }


def recommend(harness_overall: int, eval_score: int, bottleneck: str,
              min_harness: int, min_evals: int) -> str:
    if harness_overall >= max(85, min_harness) and eval_score >= max(90, min_evals):
        return "Ready for agent work. Run before/after real sessions to confirm."
    if harness_overall < min_harness:
        return f"Improve {bottleneck} subsystem (lowest score) before relying on agents."
    if eval_score < min_evals:
        return "Expand eval coverage; current harness leaves several scenarios untested."
    return "Usable with known gaps. Address them before high-stakes runs."


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a structural benchmark on a harnessed project.",
    )
    parser.add_argument("--target", default=".", help="Project root (default: '.').")
    parser.add_argument("--harness-dir", default=None)
    parser.add_argument("--output", default=None,
                        help="Where to write JSON (default: <target>/harness-benchmark.json).")
    parser.add_argument("--html", default=None,
                        help="Optional HTML report path.")
    parser.add_argument("--evals", default=None,
                        help="Override eval JSON path (default: skill's evals/evals.json).")
    parser.add_argument("--min-score", type=int, default=70)
    parser.add_argument("--min-eval-score", type=int, default=80)
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = Path(args.target).resolve()
    harness_dir = Path(args.harness_dir).resolve() if args.harness_dir else None
    eval_path = Path(args.evals).resolve() if args.evals else SKILL_ROOT / "evals" / "evals.json"

    score = score_harness(root, harness_dir=harness_dir)
    cases = load_evals(eval_path)
    coverage = eval_coverage(cases, score)
    rec = recommend(
        score.overall, coverage["score"], score.bottleneck,
        args.min_score, args.min_eval_score,
    )

    payload = {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "target": str(root),
        "harness": score.to_dict(),
        "evals": coverage,
        "recommendation": rec,
    }

    out_json = Path(args.output).resolve() if args.output else root / "harness-benchmark.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out_json}")

    if args.html:
        rows = [
            "<table><thead><tr><th>Case</th><th>Status</th></tr></thead><tbody>"
        ]
        for name in coverage["covered"]:
            rows.append(f'<tr><td>{escape_html(name)}</td><td class="pass">covered</td></tr>')
        for name in coverage["uncovered"]:
            rows.append(f'<tr><td>{escape_html(name)}</td><td class="fail">uncovered</td></tr>')
        rows.append("</tbody></table>")
        extras = (
            f'<div class="extras"><section><h2>Eval coverage '
            f'<span>{coverage["score"]}/100</span></h2>{"".join(rows)}</section>'
            f'<section><h2>Recommendation</h2>'
            f'<p>{escape_html(rec)}</p></section></div>'
        )
        out_html = Path(args.html).resolve()
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text(
            html_report(score, f"Harness Benchmark: {root.name}", extras_html=extras),
            encoding="utf-8",
        )
        print(f"Wrote {out_html}")

    print(f"\nOverall: {score.overall}/100  |  Evals: {coverage['score']}/100")
    print(f"Bottleneck: {score.bottleneck}")
    print(f"Recommendation: {rec}")

    if score.overall < args.min_score or coverage["score"] < args.min_eval_score:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
