"""
Tool definitions for Mistral AI function calling
"""

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
                        "description": "Transportation mode - choose based on user preferences: ALL (default - all modes including transit, walk, BIXI), TRANSIT (transit+walk, no bikes), WALK (walking only), BICYCLE (BIXI bike-share only), NO_BUS (metro/REM only, excludes buses), NO_METRO (bus only, excludes metro/REM). Default to ALL unless user expresses preference.",
                        "enum": ["ALL", "TRANSIT", "WALK", "BICYCLE", "NO_BUS", "NO_METRO"],
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
