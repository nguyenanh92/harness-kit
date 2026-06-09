import os
from pathlib import Path
from typing import Union, Tuple, Optional

class PromptAssembler:
    """
    Dynamically constructs the system prompt. It walks the directory tree
    upward to find custom guidelines files (e.g. CLAUDE.md, AGENTS.md) 
    and inserts them after the static prompt to preserve LLM prefix caching.
    """
    
    def __init__(self, filename_priority: list = None):
        if filename_priority is None:
            self.filename_priority = [".claudemd", "CLAUDE.md", "AGENTS.md"]
        else:
            self.filename_priority = filename_priority

    def find_guidelines_file(self, start_dir: Union[str, Path]) -> Tuple[Optional[Path], str]:
        """
        Walks up ancestor directories looking for guideline files.
        Returns the path and contents if found, otherwise (None, "").
        """
        current_dir = Path(start_dir).resolve()
        
        # Stop walking at root directory
        while True:
            for filename in self.filename_priority:
                target_path = current_dir / filename
                if target_path.is_file():
                    try:
                        with open(target_path, "r", encoding="utf-8") as f:
                            return target_path, f.read()
                    except Exception:
                        pass # Skip files that cannot be read
            
            # Move up one level
            parent_dir = current_dir.parent
            if parent_dir == current_dir:
                break
            current_dir = parent_dir
            
        return None, ""

    def assemble(self, base_system_prompt: str, workspace_dir: Union[str, Path]) -> str:
        """
        Combines static base prompt and dynamic guidelines.
        Ensures the static part is first to optimize prefix-caching.
        """
        path, guidelines = self.find_guidelines_file(workspace_dir)
        
        full_prompt = base_system_prompt
        
        if guidelines:
            full_prompt += "\n\n=== INJECTED PROJECT GUIDELINES ===\n"
            full_prompt += f"Source: {path.name}\n"
            full_prompt += "===================================\n"
            full_prompt += guidelines
            
        return full_prompt
