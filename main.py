import os
import re
import ast
from typing import Optional

import google.generativeai as genai


SYSTEM_PROMPT = """
You are a helpful personal assistant.
Be concise, clear, and friendly.
"""


class SafeCalculator:
    @staticmethod
    def eval_expr(expression: str) -> float:
        try:
            node = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise ValueError("invalid syntax") from exc

        def _eval(n):
            if isinstance(n, ast.Expression):
                return _eval(n.body)

            if isinstance(n, ast.Constant):
                if isinstance(n.value, (int, float)):
                    return n.value
                raise ValueError("only numbers are allowed")

            if isinstance(n, ast.BinOp):
                left = _eval(n.left)
                right = _eval(n.right)

                if isinstance(n.op, ast.Add):
                    return left + right
                if isinstance(n.op, ast.Sub):
                    return left - right
                if isinstance(n.op, ast.Mult):
                    return left * right
                if isinstance(n.op, ast.Div):
                    return left / right
                if isinstance(n.op, ast.Mod):
                    return left % right
                if isinstance(n.op, ast.Pow):
                    return left ** right

                raise ValueError("unsupported operator")

            if isinstance(n, ast.UnaryOp):
                operand = _eval(n.operand)

                if isinstance(n.op, ast.UAdd):
                    return +operand
                if isinstance(n.op, ast.USub):
                    return -operand

                raise ValueError("unsupported unary operator")

            raise ValueError("invalid expression")

        return _eval(node)


def detect_calculation(user_text: str) -> Optional[str]:
    text = user_text.strip().lower()

    patterns = [
        r"^calculate\s+(.+)$",
        r"^what is\s+(.+?)\??$",
        r"^solve\s+(.+)$",
        r"^([0-9\.\+\-\*\/%\(\)\s]+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, text)
        if not match:
            continue

        expr = match.group(1).strip()

        if re.fullmatch(r"[0-9\.\+\-\*\/%\(\)\s]+", expr):
            return expr

    return None


def local_fallback_reply(user_text: str) -> Optional[str]:
    text = user_text.strip().lower()

    if text in {"hi", "hello", "hey"}:
        return "Hello! How can I help you today?"

    if text in {"bye", "goodbye"}:
        return "Goodbye!"

    if "your name" in text:
        return "I am your personal assistant."

    return None


class PersonalAssistantAgent:
    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        self.model_name = model_name
        self.chat = None

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY environment variable.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=SYSTEM_PROMPT,
        )
        self.reset_chat()

    def reset_chat(self) -> None:
        self.chat = self.model.start_chat(history=[])

    def run_local_tools(self, user_text: str) -> Optional[str]:
        expr = detect_calculation(user_text)
        if expr is not None:
            try:
                result = SafeCalculator.eval_expr(expr)
                if isinstance(result, float) and result.is_integer():
                    return str(int(result))
                return str(result)
            except ZeroDivisionError:
                return "Error: division by zero."
            except ValueError as exc:
                return f"Error: invalid calculation ({exc})."
            except Exception as exc:
                return f"Error: calculation failed ({exc})."

        fallback = local_fallback_reply(user_text)
        if fallback is not None:
            return fallback

        return None

    def ask_model(self, user_text: str) -> str:
        try:
            response = self.chat.send_message(user_text)

            text = getattr(response, "text", None)
            if text and text.strip():
                return text.strip()

            return "The model returned no readable text."

        except Exception as exc:
            error_text = str(exc)

            if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                return (
                    "Gemini quota reached for the current model. "
                    "Local tools still work, but model chat is temporarily unavailable."
                )

            return f"Gemini API error: {error_text}"

    def respond(self, user_text: str) -> str:
        # ALWAYS try local tools first
        local_result = self.run_local_tools(user_text)
        if local_result is not None:
            return local_result

        # ONLY if no local tool matched, use Gemini
        return self.ask_model(user_text)


def main() -> None:
    print("Personal Assistant Agent", flush=True)
    print("Type 'exit' to quit.", flush=True)
    print("Type 'clear' to reset conversation memory.", flush=True)
    print("-" * 40, flush=True)

    try:
        agent = PersonalAssistantAgent()
    except Exception as exc:
        print(f"Startup error: {exc}", flush=True)
        return

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAssistant: Goodbye!", flush=True)
            break

        if not user_input:
            continue

        command = user_input.lower()

        if command == "exit":
            print("Assistant: Goodbye!", flush=True)
            break

        if command == "clear":
            agent.reset_chat()
            print("Assistant: Conversation memory cleared.", flush=True)
            continue

        answer = agent.respond(user_input)
        print(f"Assistant: {answer}", flush=True)


if __name__ == "__main__":
    main()