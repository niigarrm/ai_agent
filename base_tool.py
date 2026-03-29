from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name used by the registry and Gemini."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Short explanation of what the tool does."""
        pass

    @abstractmethod
    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run the tool logic with the provided arguments."""
        pass

    @abstractmethod
    def get_declaration(self) -> Dict[str, Any]:
        """Return the Gemini function-calling schema for this tool."""
        pass