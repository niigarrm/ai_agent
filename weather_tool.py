from typing import Any, Dict
import requests

from tools.base_tool import BaseTool


class WeatherTool(BaseTool):
    """
    Gets current weather for a city using Open-Meteo:
    1. Geocode city name -> latitude/longitude
    2. Request current weather data
    """

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    @property
    def name(self) -> str:
        return "weather"

    @property
    def description(self) -> str:
        return "Returns the current weather for a given city."

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        city = args.get("city")

        if not city:
            return {"error": "Missing required argument: 'city'"}

        if not isinstance(city, str):
            return {"error": "'city' must be a string"}

        try:
            location = self._get_location(city)
            if "error" in location:
                return location

            weather = self._get_weather(location["latitude"], location["longitude"])
            if "error" in weather:
                return weather

            return {
                "city": location["name"],
                "country": location.get("country"),
                "timezone": location.get("timezone"),
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "temperature_c": weather.get("temperature_2m"),
                "wind_speed_kmh": weather.get("wind_speed_10m"),
                "wind_direction": weather.get("wind_direction_10m"),
                "is_day": weather.get("is_day"),
                "weather_code": weather.get("weather_code"),
                "time": weather.get("time"),
            }

        except requests.RequestException as e:
            return {"error": f"Weather API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Failed to get weather: {str(e)}"}

    def get_declaration(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, for example Riga, Baku, or New York"
                    }
                },
                "required": ["city"]
            }
        }

    def _get_location(self, city: str) -> Dict[str, Any]:
        response = requests.get(
            self.GEOCODING_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results")
        if not results:
            return {"error": f"Could not find location: '{city}'"}

        best_match = results[0]

        return {
            "name": best_match.get("name", city),
            "country": best_match.get("country"),
            "timezone": best_match.get("timezone"),
            "latitude": best_match["latitude"],
            "longitude": best_match["longitude"],
        }

    def _get_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        response = requests.get(
            self.FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": [
                    "temperature_2m",
                    "wind_speed_10m",
                    "wind_direction_10m",
                    "weather_code",
                    "is_day",
                ],
                "timezone": "auto",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        current = data.get("current")
        if not current:
            return {"error": "No current weather data returned"}

        return current