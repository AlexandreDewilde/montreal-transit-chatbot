"""
Tools for Mistral AI function calling
"""

import requests
from typing import Any, Dict, List, Optional
from datetime import datetime


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
    },
    {
        "type": "function",
        "function": {
            "name": "plan_trip",
            "description": "Plan a trip from one location to another using various modes of transportation (transit, walking, biking, driving). Returns detailed itineraries with step-by-step directions. Common Montreal destinations: Old Montreal (45.5048, -73.5540), McGill University (45.5048, -73.5762), Mont-Royal Park (45.5048, -73.5874), Plateau Mont-Royal (45.5262, -73.5782), Jean-Talon Market (45.5356, -73.6135), Olympic Stadium (45.5579, -73.5516)",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_lat": {
                        "type": "number",
                        "description": "Starting location latitude (use user's current location from message context)",
                    },
                    "from_lon": {
                        "type": "number",
                        "description": "Starting location longitude (use user's current location from message context)",
                    },
                    "to_lat": {
                        "type": "number",
                        "description": "Destination latitude",
                    },
                    "to_lon": {
                        "type": "number",
                        "description": "Destination longitude",
                    },
                    "mode": {
                        "type": "string",
                        "description": "Transportation mode: TRANSIT (bus/metro), WALK, BICYCLE, CAR, or TRANSIT,WALK (combined)",
                        "enum": ["TRANSIT,WALK", "WALK", "BICYCLE", "CAR", "TRANSIT"],
                    },
                    "arrive_by": {
                        "type": "boolean",
                        "description": "If true, the time represents arrival time. If false (default), it represents departure time",
                    },
                    "time": {
                        "type": "string",
                        "description": "Departure or arrival time in ISO format (e.g., '2024-01-15T14:30:00'). If not provided, uses current time.",
                    },
                    "max_walk_distance": {
                        "type": "number",
                        "description": "Maximum walking distance in meters (default: 800)",
                    },
                },
                "required": ["from_lat", "from_lon", "to_lat", "to_lon"],
            },
        },
    },
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


def plan_trip(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    mode: str = "TRANSIT,WALK",
    arrive_by: bool = False,
    time: Optional[str] = None,
    max_walk_distance: float = 800,
) -> Dict[str, Any]:
    """
    Plan a trip using OpenTripPlanner 2.x GraphQL API

    Args:
        from_lat: Starting latitude
        from_lon: Starting longitude
        to_lat: Destination latitude
        to_lon: Destination longitude
        mode: Transportation mode (TRANSIT,WALK, WALK, BICYCLE, CAR)
        arrive_by: If True, time is arrival time; if False, departure time
        time: Time in ISO format, or None for current time
        max_walk_distance: Maximum walking distance in meters

    Returns:
        Dictionary with trip itineraries
    """
    try:
        # OpenTripPlanner 2.x GraphQL endpoint
        otp_url = "http://localhost:8080/otp/gtfs/v1"

        # Format time for GraphQL (use current time if not provided)
        if time:
            try:
                dt = datetime.fromisoformat(time.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.now()
        else:
            dt = datetime.now()

        # Format as ISO 8601 string for GraphQL
        time_str = dt.strftime("%Y-%m-%dT%H:%M:%S")

        # GraphQL query for trip planning (OTP 2.x syntax)
        query = f"""
        {{
          plan(
            from: {{lat: {from_lat}, lon: {from_lon}}}
            to: {{lat: {to_lat}, lon: {to_lon}}}
            numItineraries: 3
            date: "{time_str}"
            arriveBy: {"true" if arrive_by else "false"}
          ) {{
            itineraries {{
              startTime
              endTime
              duration
              walkDistance
              legs {{
                mode
                startTime
                endTime
                duration
                distance
                from {{
                  name
                  lat
                  lon
                }}
                to {{
                  name
                  lat
                  lon
                }}
                route {{
                  shortName
                  longName
                }}
                trip {{
                  tripHeadsign
                }}
              }}
            }}
          }}
        }}
        """

        payload = {
            "query": query
        }

        response = requests.post(
            otp_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()

        data = response.json()

        # Check for GraphQL errors
        if "errors" in data:
            return {"error": f"GraphQL error: {data['errors'][0].get('message', 'Unknown error')}"}

        # Extract itineraries
        plan = data.get("data", {}).get("plan", {})
        if not plan or "itineraries" not in plan or not plan["itineraries"]:
            return {"error": "No routes found for this trip"}

        itineraries = []
        for itinerary in plan["itineraries"]:
            legs = []
            for leg in itinerary.get("legs", []):
                leg_info = {
                    "mode": leg.get("mode"),
                    "from": leg.get("from", {}).get("name"),
                    "to": leg.get("to", {}).get("name"),
                    "distance": round(leg.get("distance", 0), 2),
                    "duration": leg.get("duration", 0),
                    "route": leg.get("route", {}).get("shortName") if leg.get("route") else None,
                    "routeLongName": leg.get("route", {}).get("longName") if leg.get("route") else None,
                    "headsign": leg.get("trip", {}).get("tripHeadsign") if leg.get("trip") else None,
                }
                legs.append(leg_info)

            itinerary_info = {
                "duration": itinerary.get("duration", 0),
                "duration_minutes": round(itinerary.get("duration", 0) / 60, 1),
                "walkDistance": round(itinerary.get("walkDistance", 0), 2),
                "transfers": itinerary.get("transfers", 0),
                "startTime": itinerary.get("startTime"),
                "endTime": itinerary.get("endTime"),
                "legs": legs,
            }
            itineraries.append(itinerary_info)

        return {
            "success": True,
            "from": {"lat": from_lat, "lon": from_lon},
            "to": {"lat": to_lat, "lon": to_lon},
            "itineraries": itineraries,
            "count": len(itineraries),
        }

    except requests.exceptions.ConnectionError:
        return {
            "error": "Cannot connect to OpenTripPlanner. Make sure it's running at http://localhost:8080"
        }
    except requests.exceptions.Timeout:
        return {"error": "Request to OpenTripPlanner timed out"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch route data: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


# Function registry - maps function names to actual Python functions
FUNCTION_REGISTRY = {"get_weather": get_weather, "plan_trip": plan_trip}


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
