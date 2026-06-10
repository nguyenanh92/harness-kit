from typing import List, Dict, Any

class ContextManager:
    """
    Manages the LLM context window budget. Since we enforce zero external
    dependencies, it uses a simple character-based word-ratio heuristic
    to estimate token sizes, and triggers compaction when usage exceeds the limit.
    """
    
    def __init__(self, max_tokens: int = 100000, compaction_threshold: float = 0.8):
        self.max_tokens = max_tokens
        self.compaction_threshold = compaction_threshold
        self.compaction_trigger = int(max_tokens * compaction_threshold)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        A zero-dependency token estimation heuristic.
        On average, 1 token is ~4 characters in English or ~0.75 words.
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    def calculate_total_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Estimates the total token count of a list of messages.
        """
        total = 0
        for msg in messages:
            total += self.estimate_tokens(msg.get("role", ""))
            total += self.estimate_tokens(msg.get("content", ""))
        return total

    def should_compact(self, messages: List[Dict[str, str]]) -> bool:
        """
        Checks if the current message history exceeds the compaction threshold.
        """
        total = self.calculate_total_tokens(messages)
        return total >= self.compaction_trigger

    def compact(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Reactively compacts conversation history:
        - Keeps the system prompt intact (first message if role is system).
        - Keeps the last N turns intact (e.g., last 4 turns).
        - Summarizes older turns in between.
        """
        if not self.should_compact(messages) or len(messages) <= 10:
            return messages

        system_msg = None
        start_idx = 0
        if messages[0].get("role") == "system":
            system_msg = messages[0]
            start_idx = 1

        # Keep the last 4 messages verbatim
        verbatim_count = 4
        older_messages = messages[start_idx : -verbatim_count]
        recent_messages = messages[-verbatim_count:]

        # Compress older messages into a single summary block
        summary_content = "--- [Context Compacted at Turn Threshold] ---\n"
        summary_content += "Summary of previous actions and decisions:\n"
        
        for msg in older_messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            # Truncate content in summary to avoid bloating
            snippet = content[:150] + "..." if len(content) > 150 else content
            summary_content += f"- {role}: {snippet.strip()}\n"

        summary_message = {
            "role": "system",
            "content": summary_content
        }

        # Reconstruct messages list
        compacted_list = []
        if system_msg:
            compacted_list.append(system_msg)
        compacted_list.append(summary_message)
        compacted_list.extend(recent_messages)

        return compacted_list
