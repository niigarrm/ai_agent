from typing import Any, Dict, List

from tools.base_tool import BaseTool


class ToolRegistry:
    """
    Stores available tools, exposes their Gemini declarations,
    and executes them by name.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool using its unique name.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")

        self._tools[tool.name] = tool

    def has_tool(self, tool_name: str) -> bool:
        """
        Check whether a tool exists in the registry.
        """
        return tool_name in self._tools

    def get_tool(self, tool_name: str) -> BaseTool:
        """
        Return a tool instance by name.
        """
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' is not registered.")

        return self._tools[tool_name]

    def get_tool_declarations(self) -> List[Dict[str, Any]]:
        """
        Return all tool schemas for Gemini function calling.
        """
        return [tool.get_declaration() for tool in self._tools.values()]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a registered tool safely.
        """
        if tool_name not in self._tools:
            return {
                "status": "error",
                "error": f"Unknown tool: '{tool_name}'"
            }

        tool = self._tools[tool_name]

        try:
            result = tool.execute(args)

            if not isinstance(result, dict):
                return {
                    "status": "error",
                    "error": f"Tool '{tool_name}' returned a non-dictionary result."
                }

            return {
                "status": "success",
                "tool": tool_name,
                "data": result
            }

        except Exception as e:
            return {
                "status": "error",
                "tool": tool_name,
                "error": str(e)
            }

    def list_tools(self) -> List[str]:
        """
        Return the list of registered tool names.
        """
        return list(self._tools.keys())