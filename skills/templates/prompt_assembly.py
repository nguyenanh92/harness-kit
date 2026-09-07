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

    def find_guidelines_file(
        self,
        start_dir: Union[str, Path],
        workspace_root: Optional[Union[str, Path]] = None,
    ) -> Tuple[Optional[Path], str]:
        """Walk up ancestor directories looking for a guidelines file.

        Stops at the first .git boundary or at ``workspace_root`` (whichever
        comes first) so a subagent in a nested project cannot load the parent
        repo's AGENTS.md / CLAUDE.md by accident (Gotcha #5).
        """
        current_dir = Path(start_dir).resolve()
        stop_at = Path(workspace_root).resolve() if workspace_root else current_dir

        while True:
            for filename in self.filename_priority:
                target_path = current_dir / filename
                if target_path.is_file():
                    try:
                        with open(target_path, "r", encoding="utf-8") as f:
                            return target_path, f.read()
                    except Exception:
                        pass

            # Stop at git repo boundary or declared workspace root
            if (current_dir / ".git").exists() or current_dir == stop_at:
                break

            parent_dir = current_dir.parent
            if parent_dir == current_dir:   # filesystem root guard
                break
            current_dir = parent_dir

        return None, ""

    def assemble(self, base_system_prompt: str, workspace_dir: Union[str, Path]) -> str:
        """Combine static base prompt and dynamic guidelines.

        The static part comes first to keep the LLM prefix cache intact.
        The walk is bounded to ``workspace_dir`` so it never crosses a git
        repo boundary.
        """
        path, guidelines = self.find_guidelines_file(workspace_dir, workspace_root=workspace_dir)
        
        full_prompt = base_system_prompt
        
        if guidelines:
            full_prompt += "\n\n=== INJECTED PROJECT GUIDELINES ===\n"
            full_prompt += f"Source: {path.name}\n"
            full_prompt += "===================================\n"
            full_prompt += guidelines
            
        return full_prompt
