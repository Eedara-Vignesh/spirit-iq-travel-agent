"""
backend package initialization.
SpiritIQ AI Travel Planning Agent.
"""

try:
    from backend.schemas import (
        TripRequest,
        ToolResult,
        TripPlan,
        TripType,
        TravelPace,
        TransportMode,
    )
    from backend.config import (
        settings,
        get_settings,
        mask_secret,
        test_groq_connection,
        test_gemini_connection,
    )

    __all__ = [
        "TripRequest",
        "ToolResult",
        "TripPlan",
        "TripType",
        "TravelPace",
        "TransportMode",
        "settings",
        "get_settings",
        "mask_secret",
        "test_groq_connection",
        "test_gemini_connection",
    ]
except ImportError:
    # Allows importing standalone tools (like Dijkstra) before dependencies are installed
    pass
