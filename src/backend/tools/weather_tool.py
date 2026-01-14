"""
Weather tool using Open-Meteo API
"""

import requests
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def get_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Get current weather for a location using Open-Meteo API

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location

    Returns:
        Dictionary with weather information
    """
    logger.debug(f"🌤️  Getting weather for location ({latitude}, {longitude})")
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

        logger.debug("Fetching weather from Open-Meteo API")
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

        logger.debug(
            f"✅ Weather: {result['temperature']}°C, feels like {result['feels_like']}°C"
        )

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to fetch weather data: {str(e)}")
        return {"error": f"Failed to fetch weather data: {str(e)}"}
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_weather: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}
