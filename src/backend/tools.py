"""
Tools for Mistral AI function calling
"""

import requests
from typing import Any, Dict


# Tool definitions for Mistral API
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather information for a specific location using latitude and longitude coordinates",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude of the location (e.g., 45.5017 for Montreal)",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the location (e.g., -73.5673 for Montreal)",
                    },
                },
                "required": ["latitude", "longitude"],
            },
        },
    }
]


def get_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Get current weather for a location using Open-Meteo API

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location

    Returns:
        Dictionary with weather information
    """
    try:
        # Open-Meteo API endpoint
        url = "https://api.open-meteo.com/v1/forecast"

        # Request parameters
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
            "timezone": "auto",
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract current weather
        current = data.get("current", {})

        result = {
            "temperature": current.get("temperature_2m"),
            "temperature_unit": data.get("current_units", {}).get(
                "temperature_2m", "°C"
            ),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_speed_unit": data.get("current_units", {}).get(
                "wind_speed_10m", "km/h"
            ),
            "precipitation": current.get("precipitation"),
            "weather_code": current.get("weather_code"),
            "timezone": data.get("timezone"),
            "location": f"Lat: {latitude}, Lon: {longitude}",
        }

        return result

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch weather data: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


# Function registry - maps function names to actual Python functions
FUNCTION_REGISTRY = {"get_weather": get_weather}


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool by name with given arguments

    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments to pass to the tool

    Returns:
        Result from the tool execution
    """
    if tool_name not in FUNCTION_REGISTRY:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        func = FUNCTION_REGISTRY[tool_name]
        result = func(**arguments)
        return result
    except Exception as e:
        return {"error": f"Error executing {tool_name}: {str(e)}"}
