"""
backend/tools/safety_tool.py
============================
Safety and local precautions tool.
Assigned to: Member 2 (Destination, Weather and Safety)

Provides contextual safety guidance, emergency helplines, and dynamic advisories
tailored to destination geography, climate, and traveler dynamic.
"""

from __future__ import annotations

from typing import List, Optional
from backend.schemas import ToolResult


def get_safety_precautions(
    destination: str,
    trip_type: str = "solo",
    special_requirements: Optional[str] = None,
    weather_conditions: Optional[str] = None,
    is_monsoon: bool = False,
) -> ToolResult:
    """
    Generate tailored safety advisories and emergency helplines based on
    location characteristics, group composition, and weather.
    """
    dest_lower = destination.lower()
    trip_lower = trip_type.lower()
    spec_lower = (special_requirements or "").lower()

    precautions: List[str] = [
        "National Emergency Helpline (India): Dial 112 for all police, medical, or fire emergencies.",
        f"Keep offline copies of government ID proof and hotel reservation vouchers while in {destination}.",
    ]

    # Destination-specific geography precautions
    if any(k in dest_lower for k in ["goa", "beach", "puri", "kovalam", "pondicherry", "gokarna"]):
        precautions.append("Beach safety: Only swim within designated safe zones indicated by active lifeguard flags (red flags = strictly no swimming).")
        precautions.append("Stay hydrated under direct sun; apply water-resistant SPF 50+ sunscreen and wear sunglasses.")
    elif any(k in dest_lower for k in ["manali", "shimla", "ooty", "coorg", "wayanad", "leh", "ladakh", "munnar"]):
        precautions.append("Hill driving / ghat roads: Travel during daylight hours; carry motion sickness medication if prone to car sickness.")
        precautions.append("Weather shifts rapidly in high altitude; always keep a warm outer layer accessible in daypacks.")
    elif any(k in dest_lower for k in ["jaipur", "udaipur", "jodhpur", "jaisalmer"]):
        precautions.append("Desert climate: Drink plenty of electrolyte water; protect against dry dust with sunglasses and scarves.")

    # Group composition precautions
    if "family" in trip_lower or "child" in spec_lower or "infant" in spec_lower:
        precautions.append("Family travel: Keep basic child healthcare supplies (paracetamol, oral rehydration salts, band-aids) readily available.")
    elif "elderly" in spec_lower or "senior" in spec_lower or "accessibility" in spec_lower:
        precautions.append("Accessibility advisory: Confirm wheelchair or ramp accessibility with monuments and resorts prior to arrival.")
    elif "solo" in trip_lower:
        precautions.append("Solo travel: Share your daily travel itinerary and live cab ride tracking with a trusted contact.")

    # Dietary precautions if specified
    if "veg" in spec_lower or "halal" in spec_lower or "gluten" in spec_lower or "allerg" in spec_lower:
        precautions.append("Dietary precautions: Explicitly communicate allergies or food preferences at local dining venues before ordering.")

    # Monsoon advisory
    if is_monsoon or (weather_conditions and "rain" in weather_conditions.lower()):
        precautions.append("Monsoon advisory: Keep electronics in waterproof dry-bags; watch for slippery moss on historical fort steps and trekking trails.")

    return ToolResult.ok(
        data={"precautions": precautions},
        metadata={"tool": "safety_tool", "destination": destination, "count": len(precautions)},
    )
