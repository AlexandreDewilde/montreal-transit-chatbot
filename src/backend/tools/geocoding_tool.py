"""
Geocoding tool using Photon (OpenStreetMap) geocoder
"""

import requests
import logging
from typing import Any, Dict

from config import get_settings

logger = logging.getLogger(__name__)


def geocode_location(query: str, limit: int = 1) -> Dict[str, Any]:
    """
    Convert a location name or address to geographic coordinates using Photon geocoder

    Args:
        query: Location name or address to geocode
        limit: Maximum number of results to return (default: 1)

    Returns:
        Dictionary with geocoding results containing coordinates and location info
    """
    logger.debug(f"📍 Geocoding location: '{query}' (limit={limit})")
    try:
        # Get Photon URL from settings
        settings = get_settings()
        photon_url = settings.photon_url
        api_endpoint = f"{photon_url}/api"
        logger.debug(f"Using Photon API endpoint: {api_endpoint}")

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
            logger.warning(f"⚠️  No geocoding results found for '{query}'")
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

        logger.debug(f"✅ Found {len(results)} location(s) for '{query}'")
        if results:
            logger.debug(
                f"First result: {results[0]['name']} at ({results[0]['latitude']}, {results[0]['longitude']})"
            )

        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results,
        }

    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Cannot connect to Photon geocoder at {photon_url}")
        return {
            "success": False,
            "error": f"Cannot connect to Photon geocoder at {photon_url}. Make sure it's running.",
            "query": query,
        }
    except requests.exceptions.Timeout:
        logger.error(f"❌ Geocoding request timed out for '{query}'")
        return {
            "success": False,
            "error": "Geocoding request timed out",
            "query": query,
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Geocoding request failed: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to geocode location: {str(e)}",
            "query": query,
        }
    except Exception as e:
        logger.error(
            f"❌ Unexpected error in geocode_location: {str(e)}", exc_info=True
        )
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "query": query,
        }
