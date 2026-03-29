from typing import Any, Dict, List, Optional


class MemoryManager:
    """
    Stores conversation history for the current CLI session.
    Keeps user messages, model messages, and tool responses.
    """

    def __init__(self) -> None:
        self._history: List[Dict[str, Any]] = []

    def add_user_message(self, text: str) -> None:
        self._history.append({
            "role": "user",
            "parts": [{"text": text}]
        })

    def add_model_message(self, text: str) -> None:
        self._history.append({
            "role": "model",
            "parts": [{"text": text}]
        })

    def add_model_parts(self, parts: List[Dict[str, Any]]) -> None:
        self._history.append({
            "role": "model",
            "parts": parts
        })

    def add_tool_response(
        self,
        tool_name: str,
        response: Dict[str, Any],
        tool_call_id: Optional[str] = None
    ) -> None:
        function_response = {
            "name": tool_name,
            "response": response
        }

        if tool_call_id:
            function_response["id"] = tool_call_id

        self._history.append({
            "role": "user",
            "parts": [{
                "functionResponse": function_response
            }]
        })

    def get_history(self) -> List[Dict[str, Any]]:
        return self._history.copy()

    def clear(self) -> None:
        self._history.clear()

    def last_message(self) -> Optional[Dict[str, Any]]:
        if not self._history:
            return None
        return self._history[-1]

    def __len__(self) -> int:
        return len(self._history)