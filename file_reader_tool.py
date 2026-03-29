from typing import Any, Dict
from pathlib import Path

from tools.base_tool import BaseTool


class FileReaderTool(BaseTool):
    """
    Reads text content from a local file.

    For safety, this tool only allows reading files from a specific base directory.
    Default allowed directory: ./data
    """

    def __init__(self, base_directory: str = "data") -> None:
        self.base_directory = Path(base_directory).resolve()

    @property
    def name(self) -> str:
        return "file_reader"

    @property
    def description(self) -> str:
        return "Reads the content of a local text file from the allowed data directory."

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        file_name = args.get("file_name")

        if not file_name:
            return {"error": "Missing required argument: 'file_name'"}

        if not isinstance(file_name, str):
            return {"error": "'file_name' must be a string"}

        try:
            target_path = (self.base_directory / file_name).resolve()

            # Prevent path traversal outside the allowed directory
            if not str(target_path).startswith(str(self.base_directory)):
                return {"error": "Access denied: file is outside the allowed directory"}

            if not target_path.exists():
                return {"error": f"File not found: '{file_name}'"}

            if not target_path.is_file():
                return {"error": f"'{file_name}' is not a file"}

            if target_path.suffix.lower() not in [".txt", ".md", ".csv"]:
                return {
                    "error": "Unsupported file type. Allowed types: .txt, .md, .csv"
                }

            content = target_path.read_text(encoding="utf-8")

            return {
                "file_name": file_name,
                "content": content,
                "characters": len(content),
                "lines": len(content.splitlines())
            }

        except UnicodeDecodeError:
            return {"error": f"Could not decode file '{file_name}' as UTF-8 text"}
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    def get_declaration(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Name of the file to read from the allowed data directory, for example notes.txt"
                    }
                },
                "required": ["file_name"]
            }
        }