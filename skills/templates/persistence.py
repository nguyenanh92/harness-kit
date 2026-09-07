import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Union

class SessionLogger:
    """
    Handles state durability by writing session events to disk in an
    append-only JSON Line (.jsonl) format. This ensures that even if the
    agent process crashes mid-session, all historical turns are preserved.
    """
    
    def __init__(self, log_path: Union[str, Path]):
        self.log_path = Path(log_path)
        # Ensure parent directories exist
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
    def append_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Appends a new event dictionary to the log file.
        Immediately flushes to disk to ensure write durability.
        """
        event = {
            "event_type": event_type,
            "data": data
        }
        
        # Open in append mode and write event
        with open(self.log_path, mode="a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            f.flush()  # Force write to disk immediately

    def replay_events(self) -> List[Dict[str, Any]]:
        """
        Reads the log file line-by-line to reconstruct the history
        of the current session.
        """
        if not self.log_path.exists():
            return []
            
        events = []
        with open(self.log_path, mode="r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    try:
                        events.append(json.loads(line_str))
                    except json.JSONDecodeError as exc:
                        print(
                            f"[SessionLogger] Warning: skipped malformed JSONL line: {exc}",
                            file=sys.stderr,
                        )
                        continue
        return events

    def clear(self) -> None:
        """
        Clears the session log file (useful when starting a clean session).
        """
        if self.log_path.exists():
            self.log_path.unlink()
