import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

def has_file(files_dict: Dict[str, str], names: List[str]) -> bool:
    return any(name in files_dict for name in names)

def text_has(text: str, needles: List[str]) -> bool:
    lower_text = text.lower()
    return any(needle.lower() in lower_text for needle in needles)

def validate_json_feature_list(text: str) -> bool:
    try:
        data = json.loads(text)
        features = data.get("features", [])
        if not isinstance(features, list):
            return False
        for f in features:
            if not all(k in f for k in ["id", "name", "description", "status"]):
                return False
            if not all(isinstance(f[k], str) for k in ["id", "name", "description", "status"]):
                return False
        return True
    except Exception:
        return False

def score_harness(target_dir: Path) -> Dict[str, Any]:
    # Load files
    candidates = [
        "AGENTS.md",
        "CLAUDE.md",
        "feature_list.json",
        "feature-list.json",
        "progress.md",
        "session-handoff.md",
        "init.sh"
    ]
    
    files_dict = {}
    for filename in candidates:
        filepath = target_dir / filename
        if filepath.is_file():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    files_dict[filename] = f.read()
            except Exception:
                pass
                
    all_text = "\n\n".join(f"{name}\n{content}" for name, content in files_dict.items())
    agents = files_dict.get("AGENTS.md", "") or files_dict.get("CLAUDE.md", "")
    feature_list = files_dict.get("feature_list.json", "") or files_dict.get("feature-list.json", "")
    progress = files_dict.get("progress.md", "")
    handoff = files_dict.get("session-handoff.md", "")
    init = files_dict.get("init.sh", "")
    
    checks = {
        "instructions": [
            {"pass": has_file(files_dict, ["AGENTS.md", "CLAUDE.md"]), "message": "Agent instruction file exists"},
            {"pass": text_has(agents, ["Startup Workflow", "Before writing code"]), "message": "Startup workflow documented"},
            {"pass": text_has(agents, ["Definition of Done", "done only when"]), "message": "Definition of done documented"},
            {"pass": text_has(agents, ["Verification Commands", "./init.sh", "test", "verify"]), "message": "Verification commands discoverable"},
            {"pass": text_has(agents, ["feature_list.json", "progress.md"]), "message": "State artifacts routed from instructions"}
        ],
        "state": [
            {"pass": has_file(files_dict, ["feature_list.json", "feature-list.json"]), "message": "Feature tracker exists"},
            {"pass": validate_json_feature_list(feature_list), "message": "Feature tracker is valid and has feature fields"},
            {"pass": has_file(files_dict, ["progress.md"]), "message": "Progress log exists"},
            {"pass": text_has(progress, ["Current State", "What", "Next"]), "message": "Progress log supports restart"},
            {"pass": text_has(handoff or progress, ["Blockers", "Files", "Next Session"]), "message": "Handoff captures blockers/files/next step"}
        ],
        "verification": [
            {"pass": has_file(files_dict, ["init.sh"]), "message": "Verification entrypoint exists"},
            {"pass": text_has(init, ["set -e"]), "message": "Verification fails fast"},
            {"pass": text_has(init + agents, ["test", "pytest", "vitest", "cargo test", "go test", "dotnet test"]), "message": "Test command documented"},
            {"pass": text_has(init + agents, ["build", "type", "lint", "compile"]), "message": "Static/build check documented"},
            {"pass": text_has(all_text, ["Evidence", "Verification Evidence", "command and output"]), "message": "Verification evidence is recorded"}
        ],
        "scope": [
            {"pass": text_has(agents, ["One feature at a time", "one-feature-at-a-time"]), "message": "One-feature-at-a-time rule exists"},
            {"pass": text_has(feature_list, ["dependencies"]), "message": "Feature dependencies are tracked"},
            {"pass": text_has(agents + feature_list, ["status"]), "message": "Feature status is explicit"},
            {"pass": text_has(agents, ["Stay in scope", "scope"]), "message": "Scope boundary documented"},
            {"pass": text_has(agents, ["Definition of Done"]), "message": "Completion gate limits scope closure"}
        ],
        "lifecycle": [
            {"pass": has_file(files_dict, ["init.sh"]), "message": "Startup script exists"},
            {"pass": text_has(agents, ["End of Session", "Before ending"]), "message": "End-of-session procedure exists"},
            {"pass": has_file(files_dict, ["session-handoff.md"]), "message": "Session handoff template exists"},
            {"pass": text_has(progress + handoff, ["Last Updated", "Current Objective", "Recommended Next Step"]), "message": "Session restart markers exist"},
            {"pass": text_has(agents + init, ["restartable", "clean", "Next steps"]), "message": "Clean restart path documented"}
        ]
    }
    
    subsystems = {}
    total_score = 0
    for name, subsystem_checks in checks.items():
        passed = sum(1 for c in subsystem_checks if c["pass"])
        score = max(1, round((passed / len(subsystem_checks)) * 5))
        total_score += score
        subsystems[name] = {
            "score": score,
            "passed": passed,
            "total": len(subsystem_checks),
            "checks": subsystem_checks
        }
        
    overall = round((total_score / (len(checks) * 5)) * 100)
    bottleneck = min(subsystems.keys(), key=lambda k: subsystems[k]["score"])
    
    return {
        "overall": overall,
        "bottleneck": bottleneck,
        "subsystems": subsystems
    }

def format_score_report(result: Dict[str, Any], root: str) -> str:
    lines = [
        f"Harness validation for {root}",
        f"Overall: {result['overall']}/100",
        f"Bottleneck: {result['bottleneck']}",
        ""
    ]
    for name, sub in result["subsystems"].items():
        lines.append(f"{name}: {sub['score']}/5 ({sub['passed']}/{sub['total']})")
        for check in sub["checks"]:
            lines.append(f"  {'PASS' if check['pass'] else 'FAIL'} {check['message']}")
        lines.append("")
    return "\n".join(lines)

def html_report(result: Dict[str, Any], title: str) -> str:
    def escape_html(val: str) -> str:
        return val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        
    sections = []
    for name, sub in result["subsystems"].items():
        checks_li = []
        for check in sub["checks"]:
            status_cls = "pass" if check["pass"] else "fail"
            status_text = "PASS" if check["pass"] else "FAIL"
            checks_li.append(f'<li class="{status_cls}">{status_text} {escape_html(check["message"])}</li>')
        checks_html = "\n".join(checks_li)
        
        sections.append(f"""
        <section>
          <h2>{escape_html(name)} <span>{sub["score"]}/5</span></h2>
          <ul>{checks_html}</ul>
        </section>
        """)
        
    sections_html = "\n".join(sections)
    
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape_html(title)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #172026; background: #f7f8fa; }}
    main {{ max-width: 960px; margin: 0 auto; }}
    header {{ margin-bottom: 24px; }}
    h1 {{ margin: 0 0 8px; font-size: 32px; }}
    .summary {{ display: flex; gap: 16px; flex-wrap: wrap; margin: 20px 0; }}
    .metric {{ background: white; border: 1px solid #d9dee5; border-radius: 8px; padding: 16px 18px; min-width: 180px; }}
    .metric strong {{ display: block; font-size: 28px; margin-top: 4px; }}
    section {{ background: white; border: 1px solid #d9dee5; border-radius: 8px; margin: 14px 0; padding: 16px 18px; }}
    h2 {{ margin: 0 0 10px; font-size: 20px; display: flex; justify-content: space-between; }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin: 6px 0; }}
    .pass {{ color: #126c43; }}
    .fail {{ color: #a23020; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>{escape_html(title)}</h1>
      <p>Five-subsystem harness validation report.</p>
      <div class="summary">
        <div class="metric">Overall<strong>{result["overall"]}/100</strong></div>
        <div class="metric">Bottleneck<strong>{escape_html(result["bottleneck"])}</strong></div>
      </div>
    </header>
    {sections_html}
  </main>
</body>
</html>
"""

def main():
    parser = argparse.ArgumentParser(description="Scores a project harness across five subsystems.")
    parser.add_argument("--target", type=str, default=".", help="Target directory to audit (default: '.').")
    parser.add_argument("--json", action="store_true", help="Print result in JSON format.")
    parser.add_argument("--html", type=str, help="Save report as HTML to this filepath.")
    parser.add_argument("--min-score", type=int, default=70, help="Minimum overall score required to pass (default: 70).")
    
    args = parser.parse_args()
    
    target_dir = Path(args.target).resolve()
    result = score_harness(target_dir)
    
    if args.html:
        html_path = Path(args.html).resolve()
        html_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_report(result, f"Harness Assessment: {target_dir.name}"))
            print(f"HTML report written to {html_path}")
        except Exception as e:
            print(f"Error writing HTML report: {e}")
            return 1
            
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_score_report(result, str(target_dir)))
        
    if result["overall"] < args.min_score:
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
