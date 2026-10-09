"""
backend/tools/destination_tool.py
=================================
Destination recommendation and discovery tool.
Assigned to: Member 2 (Destination, Weather and Safety)

Discovers suitable destinations matching traveler profile, budget, season, and interests.
Includes clear explanations of why each destination suits the requested travel period.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from backend.schemas import DestinationRecommendation, ToolResult

# Curated reference database of diverse Indian destinations with seasonal and climatic metadata
DESTINATIONS_DB: List[Dict[str, Any]] = [
    {
        "name": "Goa",
        "state_or_country": "Goa, India",
        "tagline": "Golden beaches, Portuguese heritage, and vibrant coastal culture",
        "climate": "coastal",
        "best_months": [10, 11, 12, 1, 2, 3],
        "monsoon_months": [6, 7, 8, 9],
        "interests": ["beaches", "seafood", "water sports", "nightlife", "heritage", "relaxation"],
        "trip_types": ["solo", "couple", "friends", "group", "family"],
        "min_budget_per_day_inr": 2500.0,
        "coordinates": {"lat": 15.2993, "lon": 74.1240},
        "highlights": ["Calangute & Baga Beaches", "Basilica of Bom Jesus", "Fort Aguada", "Dudhsagar Waterfalls"],
        "seasonal_note": "Pleasant coastal weather with moderate humidity and active water sports.",
    },
    {
        "name": "Coorg (Kodagu)",
        "state_or_country": "Karnataka, India",
        "tagline": "The Scotland of India — misty hills, coffee plantations, and waterfalls",
        "climate": "hill_station",
        "best_months": [10, 11, 12, 1, 2, 3, 4],
        "monsoon_months": [6, 7, 8, 9],
        "interests": ["nature", "coffee", "trekking", "waterfalls", "relaxation", "scenic"],
        "trip_types": ["couple", "family", "friends", "solo"],
        "min_budget_per_day_inr": 2000.0,
        "coordinates": {"lat": 12.3375, "lon": 75.8069},
        "highlights": ["Abbey Falls", "Raja's Seat", "Dubare Elephant Camp", "Coffee Plantation Walks"],
        "seasonal_note": "Crisp morning mist, lush green landscapes, and comfortable daytime temperatures (18-25°C).",
    },
    {
        "name": "Udaipur",
        "state_or_country": "Rajasthan, India",
        "tagline": "The City of Lakes — royal palaces, heritage havelis, and sunset boat rides",
        "climate": "semi_arid",
        "best_months": [10, 11, 12, 1, 2, 3],
        "monsoon_months": [7, 8],
        "interests": ["heritage", "culture", "palaces", "lakes", "photography", "local food"],
        "trip_types": ["couple", "family", "solo", "group"],
        "min_budget_per_day_inr": 2800.0,
        "coordinates": {"lat": 24.5854, "lon": 73.7125},
        "highlights": ["City Palace", "Lake Pichola boat ride", "Jag Mandir", "Saheliyon-ki-Bari"],
        "seasonal_note": "Cool, pleasant desert winter weather (12-28°C), ideal for exploring open-air palaces.",
    },
    {
        "name": "Ooty (Udhagamandalam)",
        "state_or_country": "Tamil Nadu, India",
        "tagline": "Queen of Nilgiri Hill Stations — tea gardens, toy train, and pine forests",
        "climate": "hill_station",
        "best_months": [10, 11, 12, 1, 2, 3, 4, 5],
        "monsoon_months": [6, 7, 8],
        "interests": ["nature", "tea", "mountains", "scenic", "toy train", "relaxation"],
        "trip_types": ["family", "couple", "solo", "friends"],
        "min_budget_per_day_inr": 2200.0,
        "coordinates": {"lat": 11.4102, "lon": 76.6950},
        "highlights": ["Nilgiri Mountain Railway", "Ooty Botanical Gardens", "Doddabetta Peak", "Pykara Waterfalls"],
        "seasonal_note": "Pleasant daytime chills and refreshing mountain air with blooming botanical gardens.",
    },
    {
        "name": "Jaipur",
        "state_or_country": "Rajasthan, India",
        "tagline": "The Pink City — historic forts, royal bazaars, and vibrant Rajasthani culture",
        "climate": "semi_arid",
        "best_months": [10, 11, 12, 1, 2, 3],
        "monsoon_months": [7, 8],
        "interests": ["heritage", "shopping", "food", "forts", "architecture", "culture"],
        "trip_types": ["family", "friends", "solo", "couple", "group"],
        "min_budget_per_day_inr": 2200.0,
        "coordinates": {"lat": 26.9124, "lon": 75.7873},
        "highlights": ["Amber Palace", "Hawa Mahal", "City Palace", "Jantar Mantar observatory"],
        "seasonal_note": "Mild sunny winter days (15-26°C), perfect for heritage walks and bazaar shopping.",
    },
    {
        "name": "Wayanad",
        "state_or_country": "Kerala, India",
        "tagline": "Pristine Western Ghats paradise — spice hills, wildlife sanctuaries, and waterfalls",
        "climate": "tropical_hills",
        "best_months": [10, 11, 12, 1, 2, 3, 4, 5],
        "monsoon_months": [6, 7, 8],
        "interests": ["nature", "wildlife", "trekking", "waterfalls", "spice gardens", "scenic"],
        "trip_types": ["friends", "family", "couple", "solo"],
        "min_budget_per_day_inr": 2000.0,
        "coordinates": {"lat": 11.6854, "lon": 76.1320},
        "highlights": ["Banasura Sagar Dam", "Edakkal Caves", "Chembra Peak", "Soochipara Falls"],
        "seasonal_note": "Pleasant tropical hill weather, post-monsoon waterfalls in full volume, and tea trails.",
    },
    {
        "name": "Manali",
        "state_or_country": "Himachal Pradesh, India",
        "tagline": "Himalayan adventure hub — snow-capped peaks, pine forests, and riverside cafes",
        "climate": "alpine",
        "best_months": [10, 11, 12, 1, 2, 3, 4, 5, 6],
        "monsoon_months": [7, 8],
        "interests": ["mountains", "snow", "adventure", "trekking", "rivers", "scenic"],
        "trip_types": ["friends", "couple", "solo", "group"],
        "min_budget_per_day_inr": 2600.0,
        "coordinates": {"lat": 32.2432, "lon": 77.1892},
        "highlights": ["Solang Valley", "Atal Tunnel & Sissu", "Hadimba Temple", "Old Manali Cafes"],
        "seasonal_note": "Crisp autumn turning to winter snowfall in high passes, clear Himalayan mountain skies.",
    },
    {
        "name": "Mysore (Mysuru)",
        "state_or_country": "Karnataka, India",
        "tagline": "Heritage capital — grand palaces, silk weaving, and sandalwood traditions",
        "climate": "moderate",
        "best_months": [9, 10, 11, 12, 1, 2, 3],
        "monsoon_months": [6, 7, 8],
        "interests": ["heritage", "palaces", "culture", "silk", "local food", "gardens"],
        "trip_types": ["family", "couple", "solo", "group"],
        "min_budget_per_day_inr": 1800.0,
        "coordinates": {"lat": 12.2958, "lon": 76.6394},
        "highlights": ["Mysore Palace", "Chamundi Hill", "Brindavan Gardens", "Devaraja Market"],
        "seasonal_note": "Gentle, comfortable weather (20-28°C), great for family exploration.",
    },
]


def recommend_destinations(
    origin: str,
    interests: Optional[List[str]] = None,
    budget_inr: float = 30000.0,
    travel_month: Optional[int] = None,
    trip_type: str = "solo",
    preferred_destination: Optional[str] = None,
    limit: int = 3,
) -> ToolResult:
    """
    Score and recommend destinations matching the traveler's profile.
    Provides structured DestinationRecommendation objects with clear seasonal rationale.
    """
    interests = [i.lower().strip() for i in (interests or [])]
    trip_type = trip_type.lower().strip()
    origin_clean = origin.strip().lower()

    # If the user already specified a destination, lookup exact match or create tailored recommendation
    if preferred_destination and preferred_destination.strip():
        pref = preferred_destination.strip()
        matched = next((d for d in DESTINATIONS_DB if d["name"].lower() == pref.lower()), None)
        if matched:
            rec = DestinationRecommendation(
                name=matched["name"],
                state_or_country=matched["state_or_country"],
                tagline=matched["tagline"],
                highlights=matched["highlights"],
                best_season=matched["seasonal_note"],
                estimated_cost_inr=min(budget_inr * 0.85, matched["min_budget_per_day_inr"] * 3),
            )
            return ToolResult.ok(
                data={"destinations": [rec.model_dump()], "is_user_specified": True},
                metadata={"tool": "destination_tool", "source": "catalog_match"},
            )
        else:
            rec = DestinationRecommendation(
                name=pref,
                tagline=f"Custom destination planned from {origin}",
                highlights=["Local attractions and cultural sights", "Regional cuisine"],
                best_season="Check local seasonal forecast before departure",
                estimated_cost_inr=budget_inr * 0.85,
            )
            return ToolResult.ok(
                data={"destinations": [rec.model_dump()], "is_user_specified": True},
                metadata={"tool": "destination_tool", "source": "user_specified_custom"},
            )

    # Destination Discovery Mode: Score candidates
    scored_candidates = []
    for d in DESTINATIONS_DB:
        # Don't recommend traveling to the exact same city as the origin
        if d["name"].lower() in origin_clean or origin_clean in d["name"].lower():
            continue

        score = 0.0

        # Seasonality scoring (High priority)
        if travel_month:
            if travel_month in d["best_months"]:
                score += 35.0
            elif travel_month in d["monsoon_months"]:
                score -= 15.0

        # Interests matching
        if interests:
            overlap = sum(1 for i in interests if any(i in tag or tag in i for tag in d["interests"]))
            score += overlap * 15.0

        # Trip type compatibility
        if trip_type in d["trip_types"]:
            score += 15.0

        # Budget sanity check
        daily_min = d["min_budget_per_day_inr"]
        if budget_inr >= daily_min * 2:
            score += 10.0

        reason = (
            f"Matches {trip_type} travel with focus on {', '.join(d['highlights'][:2])}. "
            f"{d['seasonal_note']}"
        )

        rec = DestinationRecommendation(
            name=d["name"],
            state_or_country=d["state_or_country"],
            tagline=d["tagline"],
            highlights=d["highlights"],
            best_season=d["seasonal_note"],
            estimated_cost_inr=min(budget_inr * 0.85, d["min_budget_per_day_inr"] * 4),
        )
        scored_candidates.append((score, rec, reason, d.get("coordinates")))

    # Sort descending by score
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    top_results = scored_candidates[:limit]

    output_list = []
    explanations = []
    coordinates_map = {}
    for _, rec, explanation, coords in top_results:
        output_list.append(rec.model_dump())
        explanations.append({"destination": rec.name, "reason": explanation})
        if coords:
            coordinates_map[rec.name] = coords

    return ToolResult.ok(
        data={
            "destinations": output_list,
            "explanations": explanations,
            "coordinates": coordinates_map,
            "is_user_specified": False,
        },
        metadata={"tool": "destination_tool", "candidates_evaluated": len(DESTINATIONS_DB)},
    )
