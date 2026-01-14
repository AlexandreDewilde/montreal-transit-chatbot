"""
Current datetime tool for Montreal timezone
"""

import logging
from typing import Any, Dict
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def get_current_datetime() -> Dict[str, Any]:
    """
    Get the current date and time in Montreal's timezone

    Returns:
        Dictionary with current datetime information in Montreal timezone
    """
    logger.debug("🕐 Getting current datetime for Montreal timezone")
    try:
        # Get current time in Montreal timezone
        montreal_tz = ZoneInfo("America/Montreal")
        now = datetime.now(montreal_tz)

        result = {
            "success": True,
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "timezone": "America/Montreal",
            "readable": now.strftime("%A, %B %d, %Y at %I:%M %p"),
        }
        logger.debug(f"✅ Current time: {result['readable']}")
        return result
    except Exception as e:
        logger.error(f"❌ Failed to get current datetime: {str(e)}")
        return {"success": False, "error": f"Failed to get current datetime: {str(e)}"}
