from typing import Any, Dict, List, Optional

from google.genai import types


class Agent:
    """
    Main AI Agent that coordinates:
    - conversation memory
    - Gemini responses
    - tool execution through the registry
    - the ReAct loop (Reason -> Act -> Observe)
    """

    def __init__(
        self,
        client: Any,
        model_name: str,
        memory_manager: Any,
        tool_registry: Any,
        system_instruction: Optional[str] = None,
        max_iterations: int = 5,
    ) -> None:
        self.client = client
        self.model_name = model_name
        self.memory_manager = memory_manager
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.system_instruction = system_instruction or (
            "You are a helpful personal assistant. "
            "Answer naturally when no tool is needed. "
            "Use tools only when necessary. "
            "When using a tool, choose the correct one and provide valid arguments."
        )

    def chat(self, user_input: str) -> str:
        """
        Main entry point for the CLI.
        Stores the user message, runs the agent loop,
        and returns the final assistant response.
        """
        self.memory_manager.add_user_message(user_input)

        last_tool_name: Optional[str] = None
        last_tool_result: Optional[Dict[str, Any]] = None

        for _ in range(self.max_iterations):
            try:
                response = self._generate_model_response()
            except Exception as e:
                error_message = f"Gemini API error: {str(e)}"
                self.memory_manager.add_model_message(error_message)
                return error_message

            function_calls = self._extract_function_calls(response)

            if function_calls:
                model_parts = self._extract_parts(response)
                if model_parts:
                    self.memory_manager.add_model_parts(model_parts)

                for function_call in function_calls:
                    tool_name = function_call["name"]
                    tool_args = function_call.get("args", {})
                    tool_id = function_call.get("id")

                    tool_result = self._execute_tool_safely(tool_name, tool_args)
                    last_tool_name = tool_name
                    last_tool_result = tool_result

                    self.memory_manager.add_tool_response(
                        tool_name=tool_name,
                        response=tool_result,
                        tool_call_id=tool_id,
                    )

                continue

            final_text = self._extract_text(response)

            if final_text:
                self.memory_manager.add_model_message(final_text)
                return final_text

            if last_tool_name and last_tool_result:
                fallback_text = self._format_tool_result(last_tool_name, last_tool_result)
                self.memory_manager.add_model_message(fallback_text)
                return fallback_text

            finish_reason = self._extract_finish_reason(response)
            fallback = f"The model returned no readable text. Finish reason: {finish_reason}"
            self.memory_manager.add_model_message(fallback)
            return fallback

        fallback = "Maximum reasoning steps reached without a final answer."
        self.memory_manager.add_model_message(fallback)
        return fallback

    def _generate_model_response(self) -> Any:
        """
        Generate a response from Gemini using memory and available tools.
        """
        contents = self.memory_manager.get_history()
        tool_declarations = self.tool_registry.get_tool_declarations()

        config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            tools=[
                types.Tool(function_declarations=tool_declarations)
            ],
        )

        return self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )

    def _execute_tool_safely(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the tool through the registry with validation and error handling.
        """
        print(f"[DEBUG] Tool requested: {tool_name}")
        print(f"[DEBUG] Tool args: {tool_args}")

        if not isinstance(tool_args, dict):
            result = {
                "status": "error",
                "tool": tool_name,
                "error": "Tool arguments must be a dictionary.",
            }
            print(f"[DEBUG] Tool result: {result}")
            return result

        try:
            result = self.tool_registry.execute_tool(tool_name, tool_args)
            print(f"[DEBUG] Tool result: {result}")
            return result
        except Exception as e:
            result = {
                "status": "error",
                "tool": tool_name,
                "error": f"Tool execution failed: {str(e)}",
            }
            print(f"[DEBUG] Tool result: {result}")
            return result

    def _extract_function_calls(self, response: Any) -> List[Dict[str, Any]]:
        """
        Extract one or more function calls from Gemini response.
        """
        extracted: List[Dict[str, Any]] = []

        try:
            function_calls = getattr(response, "function_calls", None)
            if function_calls:
                for fc in function_calls:
                    args = getattr(fc, "args", {}) or {}
                    if not isinstance(args, dict):
                        try:
                            args = dict(args)
                        except Exception:
                            args = {}

                    extracted.append(
                        {
                            "id": getattr(fc, "id", None),
                            "name": getattr(fc, "name", None),
                            "args": args,
                        }
                    )

                return [fc for fc in extracted if fc["name"]]

            candidates = getattr(response, "candidates", None)
            if not candidates:
                return extracted

            first_candidate = candidates[0]
            content = getattr(first_candidate, "content", None)
            if not content:
                return extracted

            parts = getattr(content, "parts", None)
            if not parts:
                return extracted

            for part in parts:
                function_call = getattr(part, "function_call", None)
                if function_call:
                    args = getattr(function_call, "args", {}) or {}
                    if not isinstance(args, dict):
                        try:
                            args = dict(args)
                        except Exception:
                            args = {}

                    extracted.append(
                        {
                            "id": getattr(function_call, "id", None),
                            "name": getattr(function_call, "name", None),
                            "args": args,
                        }
                    )

            return [fc for fc in extracted if fc["name"]]

        except Exception:
            return []

    def _extract_text(self, response: Any) -> str:
        """
        Extract plain text response from Gemini output.
        """
        try:
            direct_text = getattr(response, "text", None)
            if isinstance(direct_text, str) and direct_text.strip():
                return direct_text.strip()

            candidates = getattr(response, "candidates", None)
            if not candidates:
                return ""

            first_candidate = candidates[0]
            content = getattr(first_candidate, "content", None)
            if not content:
                return ""

            parts = getattr(content, "parts", None)
            if not parts:
                return ""

            texts: List[str] = []
            for part in parts:
                text_value = getattr(part, "text", None)
                if text_value:
                    texts.append(text_value)

            return "\n".join(texts).strip()

        except Exception:
            return ""

    def _extract_parts(self, response: Any) -> List[Dict[str, Any]]:
        """
        Convert model response into a list of parts that can be stored in memory.
        Useful when the model calls a tool.
        """
        result: List[Dict[str, Any]] = []

        try:
            candidates = getattr(response, "candidates", None)
            if not candidates:
                return result

            first_candidate = candidates[0]
            content = getattr(first_candidate, "content", None)
            if not content:
                return result

            parts = getattr(content, "parts", None)
            if not parts:
                return result

            for part in parts:
                text_value = getattr(part, "text", None)
                if text_value:
                    result.append({"text": text_value})
                    continue

                function_call = getattr(part, "function_call", None)
                if function_call:
                    args = getattr(function_call, "args", {}) or {}
                    if not isinstance(args, dict):
                        try:
                            args = dict(args)
                        except Exception:
                            args = {}

                    call_part = {
                        "functionCall": {
                            "name": getattr(function_call, "name", ""),
                            "args": args,
                        }
                    }

                    call_id = getattr(function_call, "id", None)
                    if call_id:
                        call_part["functionCall"]["id"] = call_id

                    thought_signature = getattr(part, "thought_signature", None)
                    if thought_signature:
                        call_part["thoughtSignature"] = thought_signature

                    result.append(call_part)

            return result

        except Exception:
            return result

    def _extract_finish_reason(self, response: Any) -> str:
        """
        Extract finish reason from Gemini response for debugging/fallback messages.
        """
        try:
            candidates = getattr(response, "candidates", None)
            if not candidates:
                return "unknown"

            first_candidate = candidates[0]
            finish_reason = getattr(first_candidate, "finish_reason", None)

            if finish_reason is None:
                return "unknown"

            return str(finish_reason)

        except Exception:
            return "unknown"

    def _format_tool_result(self, tool_name: str, tool_result: Dict[str, Any]) -> str:
        """
        Local fallback formatter when Gemini does not generate final text
        after a successful tool call.
        """
        if tool_result.get("status") == "error":
            return f"The {tool_name} tool failed: {tool_result.get('error', 'Unknown error')}"

        data = tool_result.get("data", {})

        if tool_name == "calculator":
            if "result" in data:
                return f"The result is {data['result']}."

        if tool_name == "time":
            current_time = data.get("current_time")
            timezone = data.get("timezone")
            day_of_week = data.get("day_of_week")

            if current_time and timezone:
                if day_of_week:
                    return f"The current time in {timezone} is {current_time} on {day_of_week}."
                return f"The current time in {timezone} is {current_time}."

        if tool_name == "weather":
            city = data.get("city")
            country = data.get("country")
            temperature = data.get("temperature_c")
            wind_speed = data.get("wind_speed_kmh")

            if city and temperature is not None:
                place = f"{city}, {country}" if country else city
                if wind_speed is not None:
                    return f"The current weather in {place} is {temperature}°C with wind speed of {wind_speed} km/h."
                return f"The current weather in {place} is {temperature}°C."

        if tool_name == "translator":
            translated_text = data.get("translated_text")
            if translated_text:
                return translated_text

        return f"The {tool_name} tool returned: {data}"