from typing import Callable, Dict, Any, List, Tuple

PreHookFunc = Callable[[str, Dict[str, Any]], Tuple[bool, Any]]
PostHookFunc = Callable[[str, str], None]

class HookRegistry:
    """
    Manages pre-tool and post-tool lifecycle hooks.
    Enforces the 'All-or-Nothing' trust boundary gate.
    """
    def __init__(self):
        self._pre_hooks: List[PreHookFunc] = []
        self._post_hooks: List[PostHookFunc] = []

    def register_pre_hook(self, func: PreHookFunc) -> None:
        self._pre_hooks.append(func)

    def register_post_hook(self, func: PostHookFunc) -> None:
        self._post_hooks.append(func)

    def dispatch_pre_hooks(
        self, 
        tool_name: str, 
        args: Dict[str, Any], 
        workspace_trusted: bool
    ) -> Tuple[bool, Any]:
        """
        Runs all pre-tool hooks in sequence.
        If workspace is untrusted, all hooks are skipped for safety.
        Returns (allow, modified_args_or_error_message).
        """
        if not workspace_trusted:
            # All-or-nothing bypass: skip hooks in untrusted workspaces
            return True, args

        current_args = args
        for hook in self._pre_hooks:
            try:
                allowed, result = hook(tool_name, current_args)
                if not allowed:
                    # Hook vetoed execution. 'result' is the error message.
                    return False, result
                if isinstance(result, dict):
                    # Hook modified the arguments
                    current_args = result
            except Exception as e:
                # Any hook failure halts execution for safety
                return False, f"Error executing pre-tool hook: {str(e)}"
                
        return True, current_args

    def dispatch_post_hooks(
        self, 
        tool_name: str, 
        result: str, 
        workspace_trusted: bool
    ) -> None:
        """
        Runs all post-tool hooks for auditing, logging, or telemetry.
        If workspace is untrusted, all hooks are skipped.
        """
        if not workspace_trusted:
            return

        for hook in self._post_hooks:
            try:
                hook(tool_name, result)
            except Exception:
                # Post hooks are non-blocking audit steps; fail silently
                pass
