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
      Score the harness (requires validate_harness.py on the path).

Usage from any directory in the project
-----------------------------------------
  py hk.py feature "Notification Settings"
  py hk.py start F-014
  py hk.py status
  py hk.py done
  py hk.py audit --html report.html
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# --------------------------------------------------------------------------- #
# Root resolution
# --------------------------------------------------------------------------- #

def find_root(start: Path) -> Optional[Path]:
    """Walk up from start looking for feature_list.json."""
    for p in [start, *start.parents]:
        if (p / "feature_list.json").is_file():
            return p
    return None


# --------------------------------------------------------------------------- #
# feature_list.json helpers
# --------------------------------------------------------------------------- #

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


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

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

    # Mark any existing in_progress as pending (one at a time rule)
    for f in features:
        if f.get("status") == "in_progress" and f.get("id") != fid:
            f["status"] = "pending"
            print(f"  Paused {f['id']} → pending")

    feature["status"] = "in_progress"
    data["active_feature"] = fid
    save_fl(root, data)
    print(f"→ Active: {fid} — {feature['name']}")
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

    by_status: Dict[str, List[str]] = {}
    for f in features:
        s = f.get("status", "?")
        by_status.setdefault(s, []).append(f["id"])

    counts = "  ·  ".join(f"{len(v)} {k}" for k, v in sorted(by_status.items()))
    print(f"\nQueue   {counts}  ·  {len(features)} total")

    pending = [f for f in features if f.get("status") == "pending"]
    if pending:
        print(f"Next    {pending[0]['id']} — {pending[0]['name']}")

    # Surface the recommended next step from progress.md
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

    # Run verification
    init_ps1 = root / "init.ps1"
    init_sh = root / "init.sh"

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

    # Flip status
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    feature["status"] = "done"
    feature["evidence"] = f"Verified {timestamp}: init script passed"
    save_fl(root, data)

    # Update progress.md Last Updated
    progress_md = root / "progress.md"
    if progress_md.is_file():
        text = progress_md.read_text(encoding="utf-8")
        text = re.sub(r"\*\*Last Updated:\*\*[^\n]*", f"**Last Updated:** {timestamp}", text)
        progress_md.write_text(text, encoding="utf-8")

    print(f"\n✓ {fid} done — evidence recorded, progress.md updated.")

    # Suggest next
    next_p = next((f for f in features if f.get("status") == "pending"), None)
    if next_p:
        print(f"  Next up: {next_p['id']} — {next_p['name']}")
        print(f"  Run: py hk.py start {next_p['id']}")
    return 0


def cmd_audit(args: argparse.Namespace, root: Path) -> int:
    # Look for validate_harness.py in known locations
    here = Path(__file__).resolve().parent
    candidates = [
        here / "validate_harness.py",
        root / ".harness-scripts" / "skills" / "scripts" / "validate_harness.py",
        root / ".harness-scripts" / "validate_harness.py",
        root / "skills" / "scripts" / "validate_harness.py",
    ]
    validator = next((p for p in candidates if p.is_file()), None)

    if not validator:
        print("validate_harness.py not found. Vendor it first:")
        print("  git clone --depth 1 https://github.com/nguyenanh92/harness-kit.git .harness-scripts")
        return 1

    cmd = [sys.executable, str(validator), "--target", str(root)]
    html_out = getattr(args, "html", None)
    if html_out:
        cmd += ["--html", html_out]

    result = subprocess.run(cmd, cwd=root)
    return result.returncode


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

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
    p_audit = sub.add_parser("audit", help="Score the harness (requires validate_harness.py)")
    p_audit.add_argument("--html", metavar="PATH", help="Write HTML report to PATH")

    args = parser.parse_args(argv)

    # Resolve project root
    given = Path(args.target).resolve()
    root = find_root(given) or given

    dispatch = {
        "feature": cmd_feature,
        "start":   cmd_start,
        "status":  cmd_status,
        "done":    cmd_done,
        "audit":   cmd_audit,
    }
    return dispatch[args.command](args, root)


if __name__ == "__main__":
    raise SystemExit(main())
