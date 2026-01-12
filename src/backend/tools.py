"""
Tools for Mistral AI function calling
"""

import requests
import os
from typing import Any, Dict, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from google.transit import gtfs_realtime_pb2



# Tool definitions for Mistral API
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Get the current date and time in Montreal's timezone (America/Montreal). Use this to calculate future times when user says 'tomorrow', 'next week', 'in 2 hours', etc.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "geocode_location",
            "description": "Convert a location name or address into geographic coordinates (latitude, longitude). CRITICAL: ALWAYS use this tool to convert location names to coordinates. NEVER guess or assume coordinates for destinations. This tool searches OpenStreetMap data for ALL Canadian locations, so be specific by adding city name and 'Quebec' to your query (e.g., 'Montreal, Quebec' or 'Laval, Quebec') to get accurate results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The location name or address to geocode. IMPORTANT: Always include city name and 'Quebec' for accuracy. Examples: 'Old Montreal, Montreal, Quebec', 'McGill University, Montreal, Quebec', 'Carrefour Laval, Laval, Quebec', 'Longueuil metro, Longueuil, Quebec'",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results to return (default: 1)",
                    },
                },
                "required": ["query"],
            },
        },
    },
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
            "description": "Plan a trip from one location to another using various modes of transportation (transit, walking, biking, driving). Returns detailed itineraries with step-by-step directions. IMPORTANT: Coordinates must be obtained using geocode_location tool first - do NOT use hardcoded coordinates for destinations.",
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
                        "description": "Transportation mode: TRANSIT (bus/metro/REM), WALK, BICYCLE (includes BIXI bike-share with rental stations), or TRANSIT,WALK (combined)",
                        "enum": ["TRANSIT,WALK", "WALK", "BICYCLE", "TRANSIT"],
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
    {
        "type": "function",
        "function": {
            "name": "get_stm_alerts",
            "description": "Get current STM service alerts, delays, and disruptions for metro and bus lines. Use this BEFORE planning trips to inform users of potential issues.",
            "parameters": {
                "type": "object",
                "properties": {
                    "route_type": {
                        "type": "string",
                        "description": "Filter by route type: 'metro', 'bus', or 'all' (default)",
                        "enum": ["metro", "bus", "all"],
                    },
                },
            },
        },
    },
]


def get_current_datetime() -> Dict[str, Any]:
    """
    Get the current date and time in Montreal's timezone

    Returns:
        Dictionary with current datetime information in Montreal timezone
    """
    try:
        # Get current time in Montreal timezone
        montreal_tz = ZoneInfo("America/Montreal")
        now = datetime.now(montreal_tz)

        return {
            "success": True,
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "timezone": "America/Montreal",
            "readable": now.strftime("%A, %B %d, %Y at %I:%M %p"),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get current datetime: {str(e)}"
        }


def geocode_location(query: str, limit: int = 1) -> Dict[str, Any]:
    """
    Convert a location name or address to geographic coordinates using Photon geocoder

    Args:
        query: Location name or address to geocode
        limit: Maximum number of results to return (default: 1)

    Returns:
        Dictionary with geocoding results containing coordinates and location info
    """
    try:
        # Get Photon URL from environment
        photon_url = os.getenv("PHOTON_URL", "http://localhost:2322")
        api_endpoint = f"{photon_url}/api"

        # Request parameters
        params = {
            "q": query,
            "limit": min(limit, 5),  # Cap at 5 results
        }

        response = requests.get(api_endpoint, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract features
        features = data.get("features", [])

        if not features:
            return {
                "success": False,
                "error": f"No results found for '{query}'",
                "query": query,
            }

        # Format results
        results = []
        for feature in features:
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [])

            if len(coords) >= 2:
                result = {
                    "name": props.get("name", query),
                    "latitude": coords[1],  # GeoJSON is [lon, lat]
                    "longitude": coords[0],
                    "type": props.get("type", "unknown"),
                    "city": props.get("city"),
                    "state": props.get("state"),
                    "country": props.get("country"),
                    "osm_type": props.get("osm_type"),
                    "osm_id": props.get("osm_id"),
                }
                results.append(result)

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results,
        }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": f"Cannot connect to Photon geocoder at {photon_url}. Make sure it's running.",
            "query": query,
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Geocoding request timed out",
            "query": query,
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to geocode location: {str(e)}",
            "query": query,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "query": query,
        }


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
    Plan a trip using OpenTripPlanner 2.x GraphQL API with BIXI support

    Args:
        from_lat: Starting latitude
        from_lon: Starting longitude
        to_lat: Destination latitude
        to_lon: Destination longitude
        mode: Transportation mode (TRANSIT,WALK, WALK, BICYCLE with BIXI)
        arrive_by: If True, time is arrival time; if False, departure time
        time: Time in ISO format, or None for current time
        max_walk_distance: Maximum walking distance in meters

    Returns:
        Dictionary with trip itineraries including BIXI options
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

        # Build transportModes based on requested mode
        # IMPORTANT: Always include BICYCLE with RENT qualifier to get BIXI options
        transport_modes = []
        if mode == "WALK":
            transport_modes = ["{mode: WALK}"]
        elif mode == "BICYCLE":
            transport_modes = ["{mode: BICYCLE, qualifier: RENT}", "{mode: WALK}"]
        else:  # TRANSIT,WALK or TRANSIT (default) - include BIXI as option
            transport_modes = ["{mode: WALK}", "{mode: TRANSIT}", "{mode: BICYCLE, qualifier: RENT}"]

        transport_modes_str = ", ".join(transport_modes)

        # GraphQL query for trip planning (OTP 2.x syntax)
        query = f"""
        {{
          plan(
            from: {{lat: {from_lat}, lon: {from_lon}}}
            to: {{lat: {to_lat}, lon: {to_lon}}}
            transportModes: [{transport_modes_str}]
            numItineraries: 5
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
                rentedBike
                from {{
                  name
                  lat
                  lon
                  bikeRentalStation {{
                    stationId
                    name
                    bikesAvailable
                    spacesAvailable
                  }}
                }}
                to {{
                  name
                  lat
                  lon
                  bikeRentalStation {{
                    stationId
                    name
                    bikesAvailable
                    spacesAvailable
                  }}
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
                # Convert timestamps from epoch milliseconds to readable format
                start_time_ms = leg.get("startTime")
                end_time_ms = leg.get("endTime")

                # Convert to datetime objects and format as readable strings
                start_time_readable = None
                end_time_readable = None
                if start_time_ms:
                    start_dt = datetime.fromtimestamp(start_time_ms / 1000, tz=ZoneInfo("America/Montreal"))
                    start_time_readable = start_dt.strftime("%H:%M")  # e.g., "14:35"
                if end_time_ms:
                    end_dt = datetime.fromtimestamp(end_time_ms / 1000, tz=ZoneInfo("America/Montreal"))
                    end_time_readable = end_dt.strftime("%H:%M")

                # Extract BIXI station info if available
                from_station = leg.get("from", {}).get("bikeRentalStation")
                to_station = leg.get("to", {}).get("bikeRentalStation")

                leg_info = {
                    "mode": leg.get("mode"),
                    "from": leg.get("from", {}).get("name"),
                    "to": leg.get("to", {}).get("name"),
                    "distance": round(leg.get("distance", 0), 2),
                    "duration": leg.get("duration", 0),
                    "duration_minutes": round(leg.get("duration", 0) / 60, 1),
                    "startTime": start_time_readable,  # Now in HH:MM format
                    "endTime": end_time_readable,      # Now in HH:MM format
                    "route": leg.get("route", {}).get("shortName") if leg.get("route") else None,
                    "routeLongName": leg.get("route", {}).get("longName") if leg.get("route") else None,
                    "headsign": leg.get("trip", {}).get("tripHeadsign") if leg.get("trip") else None,
                    "rentedBike": leg.get("rentedBike", False),
                }

                # Add BIXI station info if this leg involves bike rental
                if from_station:
                    leg_info["fromBixiStation"] = {
                        "stationId": from_station.get("stationId"),
                        "name": from_station.get("name"),
                        "bikesAvailable": from_station.get("bikesAvailable"),
                        "spacesAvailable": from_station.get("spacesAvailable"),
                    }

                if to_station:
                    leg_info["toBixiStation"] = {
                        "stationId": to_station.get("stationId"),
                        "name": to_station.get("name"),
                        "bikesAvailable": to_station.get("bikesAvailable"),
                        "spacesAvailable": to_station.get("spacesAvailable"),
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


def get_stm_alerts(route_type: str = "all") -> Dict[str, Any]:
    """
    Get current STM service alerts and disruptions using GTFS-RT

    Args:
        route_type: Filter by 'metro', 'bus', or 'all'

    Returns:
        Dictionary with current alerts and disruptions
    """
    try:
        # Get API key from environment
        api_key = os.getenv("STM_API_KEY")

        if not api_key:
            return {
                "error": "STM_API_KEY not set. Get your API key at: https://portail.developpeurs.stm.info/apihub"
            }

        # STM GTFS-RT Trip Updates endpoint (contains delay/alert information)
        # Note: serviceAlerts endpoint is not available, we extract delays from tripUpdates
        alerts_url = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/tripUpdates"

        headers = {
            "apikey": api_key
        }

        response = requests.get(alerts_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse GTFS-RT protobuf data
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)

        # Extract delays from trip updates
        delays = {}  # route_id -> list of delays

        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip_update = entity.trip_update

                if trip_update.HasField('trip') and trip_update.trip.HasField('route_id'):
                    route_id = trip_update.trip.route_id

                    # Check for delays in stop_time_updates
                    for stop_update in trip_update.stop_time_update:
                        if stop_update.HasField('arrival') and stop_update.arrival.HasField('delay'):
                            delay_seconds = stop_update.arrival.delay

                            # Only report significant delays (> 2 minutes)
                            if abs(delay_seconds) > 120:
                                if route_id not in delays:
                                    delays[route_id] = []
                                delays[route_id].append(delay_seconds)

        # Convert delays to alerts
        alerts = []
        for route_id, delay_list in delays.items():
            # Determine route type
            route_types = set()
            if route_id in ['1', '2', '4', '5']:
                route_types.add('metro')
            else:
                route_types.add('bus')

            # Filter by route type
            if route_type == 'metro' and 'metro' not in route_types:
                continue
            elif route_type == 'bus' and 'bus' not in route_types:
                continue

            # Calculate average delay
            avg_delay = sum(delay_list) / len(delay_list)
            max_delay = max(delay_list)

            # Create alert message
            delay_minutes = int(avg_delay / 60)
            max_delay_minutes = int(max_delay / 60)

            if avg_delay > 0:
                header = f"Delays on route {route_id}"
                description = f"Average delay: {delay_minutes} minutes (max: {max_delay_minutes} minutes)"
            else:
                header = f"Route {route_id} running ahead of schedule"
                description = f"Average: {abs(delay_minutes)} minutes early"

            alert_info = {
                'id': f'delay_{route_id}',
                'header': header,
                'description': description,
                'cause': 'UNKNOWN_CAUSE',
                'effect': 'SIGNIFICANT_DELAYS' if avg_delay > 0 else 'OTHER_EFFECT',
                'affected_routes': [route_id],
                'route_types': list(route_types),
                'avg_delay_seconds': int(avg_delay),
                'max_delay_seconds': int(max_delay),
                'num_delayed_stops': len(delay_list),
            }
            alerts.append(alert_info)

        return {
            'success': True,
            'count': len(alerts),
            'alerts': alerts,
            'filter': route_type,
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch STM alerts: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


# Function registry - maps function names to actual Python functions
FUNCTION_REGISTRY = {
    "get_current_datetime": get_current_datetime,
    "geocode_location": geocode_location,
    "get_weather": get_weather,
    "plan_trip": plan_trip,
    "get_stm_alerts": get_stm_alerts,
}


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
