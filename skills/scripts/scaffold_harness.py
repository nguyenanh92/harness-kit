import os
import shutil
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Scaffold the Python Agent Harness into a target directory.")
    parser.add_argument("--target", type=str, default="harness", help="Target subdirectory to write templates (default: 'harness').")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files in target directory.")
    
    args = parser.parse_args()
    
    # Locate templates directory
    script_dir = Path(__file__).resolve().parent
    templates_dir = script_dir.parent / "templates"
    
    if not templates_dir.exists():
        print(f"Error: Templates directory not found at {templates_dir}")
        return 1
        
    target_dir = Path(args.target).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Scaffolding Python Harness into: {target_dir}")
    
    code_templates = [
        "harness.py",
        "context_manager.py",
        "tool_registry.py",
        "persistence.py",
        "hooks.py",
        "subagent.py",
        "prompt_assembly.py"
    ]
    governance_templates = [
        "AGENTS.md",
        "feature_list.json",
        "progress.md",
        "session-handoff.md",
        "init.sh",
        "init.ps1"
    ]
    templates = code_templates + governance_templates

    copied_count = 0
    skipped_count = 0

    for filename in templates:
        src_file = templates_dir / filename
        dest_file = target_dir / filename
        
        if dest_file.exists() and not args.force:
            print(f"Skipped: {dest_file.name} (already exists, use --force to overwrite)")
            skipped_count += 1
            continue
            
        try:
            shutil.copy2(src_file, dest_file)
            print(f"Created: {dest_file.name}")
            copied_count += 1
        except Exception as e:
            print(f"Error copying {filename}: {e}")
            return 1
            
    print("-" * 40)
    print(f"Scaffolding complete. Copied: {copied_count}, Skipped: {skipped_count}")
    return 0

if __name__ == "__main__":
    exit(main())
