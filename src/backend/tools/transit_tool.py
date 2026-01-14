"""
STM transit alerts tool using GTFS-RT
"""

import requests
import logging
from typing import Any, Dict
from google.transit import gtfs_realtime_pb2  # type: ignore[import-untyped]

from config import get_settings

logger = logging.getLogger(__name__)


def get_stm_alerts(route_type: str = "all") -> Dict[str, Any]:
    """
    Get current STM service alerts and disruptions using GTFS-RT

    Args:
        route_type: Filter by 'metro', 'bus', or 'all'

    Returns:
        Dictionary with current alerts and disruptions
    """
    logger.debug(f"🚨 Getting STM alerts (filter: {route_type})")
    try:
        # Get API key from settings
        settings = get_settings()
        api_key = settings.stm_api_key

        if not api_key:
            logger.error("❌ STM_API_KEY not set in settings")
            return {
                "error": "STM_API_KEY not set. Get your API key at: https://portail.developpeurs.stm.info/apihub"
            }

        # STM GTFS-RT Trip Updates endpoint (contains delay/alert information)
        # Note: serviceAlerts endpoint is not available, we extract delays from tripUpdates
        alerts_url = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/tripUpdates"

        headers = {"apikey": api_key}

        logger.debug(f"Fetching STM GTFS-RT data from {alerts_url}")
        response = requests.get(alerts_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse GTFS-RT protobuf data
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        logger.debug(f"Parsed {len(feed.entity)} GTFS-RT entities")

        # Extract delays from trip updates
        delays = {}  # route_id -> list of delays

        for entity in feed.entity:
            if entity.HasField("trip_update"):
                trip_update = entity.trip_update

                if trip_update.HasField("trip") and trip_update.trip.HasField(
                    "route_id"
                ):
                    route_id = trip_update.trip.route_id

                    # Check for delays in stop_time_updates
                    for stop_update in trip_update.stop_time_update:
                        if stop_update.HasField(
                            "arrival"
                        ) and stop_update.arrival.HasField("delay"):
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
            if route_id in ["1", "2", "4", "5"]:
                route_types.add("metro")
            else:
                route_types.add("bus")

            # Filter by route type
            if route_type == "metro" and "metro" not in route_types:
                continue
            elif route_type == "bus" and "bus" not in route_types:
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
                "id": f"delay_{route_id}",
                "header": header,
                "description": description,
                "cause": "UNKNOWN_CAUSE",
                "effect": "SIGNIFICANT_DELAYS" if avg_delay > 0 else "OTHER_EFFECT",
                "affected_routes": [route_id],
                "route_types": list(route_types),
                "avg_delay_seconds": int(avg_delay),
                "max_delay_seconds": int(max_delay),
                "num_delayed_stops": len(delay_list),
            }
            alerts.append(alert_info)

        logger.debug(f"✅ Found {len(alerts)} STM alert(s) for {route_type}")
        if alerts:
            logger.debug(f"Affected routes: {[a['affected_routes'] for a in alerts]}")

        return {
            "success": True,
            "count": len(alerts),
            "alerts": alerts,
            "filter": route_type,
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to fetch STM alerts: {str(e)}")
        return {"error": f"Failed to fetch STM alerts: {str(e)}"}
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_stm_alerts: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}
