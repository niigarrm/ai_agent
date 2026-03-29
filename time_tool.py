from typing import Any, Dict
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tools.base_tool import BaseTool


class TimeTool(BaseTool):
    """
    Returns the current time in a given timezone.
    Example timezones:
    - UTC
    - Europe/Riga
    - Asia/Baku
    - America/New_York
    """

    @property
    def name(self) -> str:
        return "time"

    @property
    def description(self) -> str:
        return "Returns the current date and time for a given timezone."

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        timezone_name = args.get("timezone", "UTC")

        if not isinstance(timezone_name, str):
            return {"error": "'timezone' must be a string"}

        try:
            tz = ZoneInfo(timezone_name)
            current_time = datetime.now(tz)

            return {
                "timezone": timezone_name,
                "current_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "day_of_week": current_time.strftime("%A"),
                "utc_offset": current_time.strftime("%z"),
                "iso_time": current_time.isoformat()
            }

        except ZoneInfoNotFoundError:
            return {"error": f"Unknown timezone: '{timezone_name}'"}
        except Exception as e:
            return {"error": f"Failed to get time: {str(e)}"}

    def get_declaration(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone name such as UTC, Europe/Riga, Asia/Baku, or America/New_York"
                    }
                },
                "required": []
            }
        }