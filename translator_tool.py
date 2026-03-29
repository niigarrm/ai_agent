from typing import Any, Dict

from tools.base_tool import BaseTool


class TranslatorTool(BaseTool):
    """
    Translates text using the already-configured Gemini client.
    """

    def __init__(self, client: Any, model_name: str = "gemini-2.5-flash-lite") -> None:
        self.client = client
        self.model_name = model_name

    @property
    def name(self) -> str:
        return "translator"

    @property
    def description(self) -> str:
        return "Translates text from one language to another."

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        text = args.get("text")
        source_language = args.get("source_language", "auto")
        target_language = args.get("target_language")

        if not text:
            return {"error": "Missing required argument: 'text'"}
        if not target_language:
            return {"error": "Missing required argument: 'target_language'"}

        if not isinstance(text, str):
            return {"error": "'text' must be a string"}
        if not isinstance(source_language, str):
            return {"error": "'source_language' must be a string"}
        if not isinstance(target_language, str):
            return {"error": "'target_language' must be a string"}

        prompt = (
            f"Translate the following text.\n"
            f"Source language: {source_language}\n"
            f"Target language: {target_language}\n"
            f"Return only the translated text, with no explanation.\n\n"
            f"Text: {text}"
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

            translated_text = getattr(response, "text", None)
            if not translated_text or not translated_text.strip():
                return {"error": "Translation model returned no text"}

            return {
                "source_language": source_language.lower(),
                "target_language": target_language.lower(),
                "original_text": text,
                "translated_text": translated_text.strip(),
            }

        except Exception as e:
            return {"error": f"Translation failed: {str(e)}"}

    def get_declaration(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to translate"
                    },
                    "source_language": {
                        "type": "string",
                        "description": "Source language code or name, such as en, English, es, or auto"
                    },
                    "target_language": {
                        "type": "string",
                        "description": "Target language code or name, such as es, Spanish, ru, or Russian"
                    }
                },
                "required": ["text", "target_language"]
            }
        }