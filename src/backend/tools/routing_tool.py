"""
Trip planning tool using OpenTripPlanner GraphQL API
"""

import requests
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from config import get_settings

logger = logging.getLogger(__name__)


def plan_trip(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    mode: str = "ALL",
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
        mode: Transportation mode options:
            - "ALL" (default): All modes (transit, walk, BIXI)
            - "TRANSIT": Transit + walk (no BIXI)
            - "TRANSIT_BIXI": Transit + walk + BIXI (same as ALL)
            - "WALK": Walking only
            - "BICYCLE": BIXI bike-share only
            - "NO_BUS": Metro/REM + walk + BIXI (no buses)
            - "NO_METRO": Bus + walk + BIXI (no metro)
        arrive_by: If True, time is arrival time; if False, departure time
        time: Time in ISO format, or None for current time
        max_walk_distance: Maximum walking distance in meters

    Returns:
        Dictionary with trip itineraries including BIXI options
    """
    logger.info(
        f"🚌 Planning trip: ({from_lat}, {from_lon}) -> ({to_lat}, {to_lon}) [mode={mode}]"
    )
    try:
        # Get OTP URL from settings
        settings = get_settings()
        otp_url = settings.otp_url

        # Format time for GraphQL (use current time if not provided)
        if time:
            try:
                dt: datetime = datetime.fromisoformat(time.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.now()
        else:
            dt = datetime.now()

        # Format as ISO 8601 string for GraphQL
        time_str = dt.strftime("%Y-%m-%dT%H:%M:%S")

        # Build transportModes based on requested mode
        transport_modes_str = _build_transport_modes(mode)

        # Build GraphQL query
        query = _build_graphql_query(
            from_lat=from_lat,
            from_lon=from_lon,
            to_lat=to_lat,
            to_lon=to_lon,
            transport_modes_str=transport_modes_str,
            time_str=time_str,
            arrive_by=arrive_by,
        )

        payload = {"query": query}

        logger.debug(f"Sending GraphQL request to OTP at {otp_url}")
        response = requests.post(
            otp_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        # Check for GraphQL errors
        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown error")
            logger.error(f"❌ OTP GraphQL error: {error_msg}")
            return {"error": f"GraphQL error: {error_msg}"}

        # Extract itineraries
        plan = data.get("data", {}).get("plan", {})
        if not plan or "itineraries" not in plan or not plan["itineraries"]:
            logger.warning("⚠️  No routes found for this trip")
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
                    start_dt = datetime.fromtimestamp(
                        start_time_ms / 1000, tz=ZoneInfo("America/Montreal")
                    )
                    start_time_readable = start_dt.strftime("%H:%M")  # e.g., "14:35"
                if end_time_ms:
                    end_dt = datetime.fromtimestamp(
                        end_time_ms / 1000, tz=ZoneInfo("America/Montreal")
                    )
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
                    "endTime": end_time_readable,  # Now in HH:MM format
                    "route": leg.get("route", {}).get("shortName")
                    if leg.get("route")
                    else None,
                    "routeLongName": leg.get("route", {}).get("longName")
                    if leg.get("route")
                    else None,
                    "headsign": leg.get("trip", {}).get("tripHeadsign")
                    if leg.get("trip")
                    else None,
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

        logger.debug(f"✅ Found {len(itineraries)} itinerary option(s)")
        durations = [f"{it['duration_minutes']} min" for it in itineraries]
        logger.debug(f"Trip durations: {durations}")

        return {
            "success": True,
            "from": {"lat": from_lat, "lon": from_lon},
            "to": {"lat": to_lat, "lon": to_lon},
            "itineraries": itineraries,
            "count": len(itineraries),
        }

    except requests.exceptions.ConnectionError:
        settings = get_settings()
        logger.error(f"❌ Cannot connect to OpenTripPlanner at {settings.otp_url}")
        return {
            "error": f"Cannot connect to OpenTripPlanner. Make sure it's running at {settings.otp_url}"
        }
    except requests.exceptions.Timeout:
        logger.error("❌ Request to OpenTripPlanner timed out")
        return {"error": "Request to OpenTripPlanner timed out"}
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to fetch route data: {str(e)}")
        return {"error": f"Failed to fetch route data: {str(e)}"}
    except Exception as e:
        logger.error(f"❌ Unexpected error in plan_trip: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}


def _build_transport_modes(mode: str) -> str:
    """
    Build the transportModes array string based on the requested mode.

    Args:
        mode: Transportation mode preference

    Returns:
        Comma-separated string of transport mode objects for GraphQL
    """
    mode = mode.upper()

    if mode == "WALK":
        transport_modes = ["{mode: WALK}"]
    elif mode == "BICYCLE":
        # BIXI only (bike-share with walk to/from stations)
        transport_modes = ["{mode: BICYCLE, qualifier: RENT}", "{mode: WALK}"]
    elif mode == "TRANSIT":
        # Transit + walk (no BIXI)
        transport_modes = ["{mode: WALK}", "{mode: TRANSIT}"]
    elif mode == "NO_BUS":
        # Metro/REM only (no buses), with walk and BIXI
        transport_modes = [
            "{mode: WALK}",
            "{mode: RAIL}",  # Metro and REM
            "{mode: SUBWAY}",  # Metro specifically
            "{mode: BICYCLE, qualifier: RENT}",
        ]
    elif mode == "NO_METRO":
        # Bus only (no metro/REM), with walk and BIXI
        transport_modes = [
            "{mode: WALK}",
            "{mode: BUS}",
            "{mode: BICYCLE, qualifier: RENT}",
        ]
    else:  # "ALL", "TRANSIT_BIXI", or default
        # All modes: transit (bus, metro, REM), walk, and BIXI
        transport_modes = [
            "{mode: WALK}",
            "{mode: TRANSIT}",
            "{mode: BICYCLE, qualifier: RENT}",
        ]

    return ", ".join(transport_modes)


def _build_graphql_query(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    transport_modes_str: str,
    time_str: str,
    arrive_by: bool,
) -> str:
    """
    Build the GraphQL query for trip planning.

    Args:
        from_lat: Starting latitude
        from_lon: Starting longitude
        to_lat: Destination latitude
        to_lon: Destination longitude
        transport_modes_str: Comma-separated transport modes string
        time_str: ISO datetime string
        arrive_by: Whether time is arrival time

    Returns:
        Formatted GraphQL query string
    """
    return f"""
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
