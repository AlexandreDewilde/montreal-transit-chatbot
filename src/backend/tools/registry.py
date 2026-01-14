"""
Function registry for tool execution
"""

import logging
from typing import Any, Dict

from .datetime_tool import get_current_datetime
from .geocoding_tool import geocode_location
from .weather_tool import get_weather
from .routing_tool import plan_trip
from .transit_tool import get_stm_alerts

logger = logging.getLogger(__name__)

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
        logger.error(f"❌ Unknown tool requested: {tool_name}")
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        logger.debug(f"Executing tool: {tool_name}")
        func = FUNCTION_REGISTRY[tool_name]
        result = func(**arguments)
        return result
    except Exception as e:
        logger.error(f"❌ Error executing {tool_name}: {str(e)}", exc_info=True)
        return {"error": f"Error executing {tool_name}: {str(e)}"}
