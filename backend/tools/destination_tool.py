"""
backend/tools/destination_tool.py
=================================
Destination recommendation and discovery tool.
Assigned to: Member 2 (Destination, Weather and Safety)

Discovers suitable destinations matching traveler profile, budget, season, and interests.
Includes clear explanations of why each destination suits the requested travel period.
"""

from __future__ import annotations

import re
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
        "name": "Kerala",
        "state_or_country": "Kerala, India",
        "tagline": "God's Own Country — emerald backwaters, spice plantations, and Ayurvedic wellness",
        "climate": "tropical_coastal",
        "best_months": [9, 10, 11, 12, 1, 2, 3],
        "monsoon_months": [6, 7, 8],
        "interests": ["beaches", "relaxation", "nature", "local food", "culture", "waterfalls"],
        "trip_types": ["family", "couple", "group", "solo", "friends"],
        "min_budget_per_day_inr": 2400.0,
        "coordinates": {"lat": 9.9312, "lon": 76.2673},
        "highlights": ["Alleppey Houseboat Backwaters", "Fort Kochi Chinese Fishing Nets", "Munnar Tea Gardens", "Periyar Wildlife Sanctuary"],
        "seasonal_note": "Balmy tropical breezes, tranquil backwaters, and pristine post-monsoon greenery.",
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
        "name": "Shimla",
        "state_or_country": "Himachal Pradesh, India",
        "tagline": "Queen of the Hills — colonial architecture, pine-covered ridges, and snowy peaks",
        "climate": "alpine",
        "best_months": [10, 11, 12, 1, 2, 3, 4, 5, 6],
        "monsoon_months": [7, 8],
        "interests": ["mountains", "heritage", "scenic", "relaxation", "photography"],
        "trip_types": ["family", "couple", "friends", "solo"],
        "min_budget_per_day_inr": 2500.0,
        "coordinates": {"lat": 31.1048, "lon": 77.1734},
        "highlights": ["The Ridge & Christ Church", "Mall Road & Lakkar Bazaar", "Jakhoo Hill & Temple", "Kufri Winter Park"],
        "seasonal_note": "Cool mountain breeze with clear panoramic Himalayan views and scenic colonial heritage.",
    },
    {
        "name": "Varanasi",
        "state_or_country": "Uttar Pradesh, India",
        "tagline": "Spiritual heart of India — ancient ghats, sacred rituals, and silk weaving traditions",
        "climate": "plains",
        "best_months": [10, 11, 12, 1, 2, 3],
        "monsoon_months": [7, 8, 9],
        "interests": ["culture", "heritage", "local food", "photography", "temples"],
        "trip_types": ["solo", "family", "couple", "group"],
        "min_budget_per_day_inr": 1800.0,
        "coordinates": {"lat": 25.3176, "lon": 82.9739},
        "highlights": ["Dashashwamedh Ghat Evening Aarti", "Sunrise Ganges Boat Row", "Kashi Vishwanath Corridor", "Sarnath Buddhist Stupas"],
        "seasonal_note": "Crisp morning fog, comfortable winter afternoons (14-25°C), optimal for ghat exploration.",
    },
    {
        "name": "Pondicherry (Puducherry)",
        "state_or_country": "Puducherry, India",
        "tagline": "French Riviera of the East — pastel colonial villas, serene beaches, and bohemian cafes",
        "climate": "coastal",
        "best_months": [10, 11, 12, 1, 2, 3],
        "monsoon_months": [7, 8, 9],
        "interests": ["beaches", "heritage", "relaxation", "local food", "culture"],
        "trip_types": ["couple", "solo", "friends", "family"],
        "min_budget_per_day_inr": 2300.0,
        "coordinates": {"lat": 11.9416, "lon": 79.8083},
        "highlights": ["White Town French Quarter Walk", "Promenade Beach", "Auroville & Matrimandir", "Paradise Beach Ferry"],
        "seasonal_note": "Pleasant coastal weather, light ocean breeze, and comfortable evening promenade walks.",
    },
    {
        "name": "Rishikesh",
        "state_or_country": "Uttarakhand, India",
        "tagline": "Yoga capital & Himalayan gateway — sacred Ganga rapids, suspension bridges, and ashrams",
        "climate": "sub_tropical_hills",
        "best_months": [9, 10, 11, 12, 2, 3, 4, 5],
        "monsoon_months": [7, 8],
        "interests": ["adventure", "mountains", "culture", "trekking", "water sports"],
        "trip_types": ["friends", "solo", "couple", "group"],
        "min_budget_per_day_inr": 2000.0,
        "coordinates": {"lat": 30.0869, "lon": 78.2676},
        "highlights": ["Triveni Ghat Evening Aarti", "Ganges White Water Rafting", "Ram & Laxman Jhula", "Beatles Ashram Trail"],
        "seasonal_note": "Clear emerald river waters, refreshing Himalayan breeze, and peak rafting season.",
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
    {
        "name": "Agra",
        "state_or_country": "Uttar Pradesh, India",
        "tagline": "City of Mughal wonders — timeless marble mausoleums and imperial fortresses",
        "climate": "plains",
        "best_months": [10, 11, 12, 1, 2, 3],
        "monsoon_months": [7, 8],
        "interests": ["heritage", "architecture", "photography", "culture", "local food"],
        "trip_types": ["family", "couple", "solo", "group"],
        "min_budget_per_day_inr": 2400.0,
        "coordinates": {"lat": 27.1767, "lon": 78.0081},
        "highlights": ["Taj Mahal at Sunrise", "Agra Fort", "Mehtab Bagh Sunset", "Fatehpur Sikri"],
        "seasonal_note": "Pleasant sunny winter climate (12-24°C), ideal for exploring open marble courtyards.",
    },
    {
        "name": "Hampi",
        "state_or_country": "Karnataka, India",
        "tagline": "UNESCO World Heritage boulder kingdom — ruined temples and Vijayanagara glory",
        "climate": "semi_arid",
        "best_months": [10, 11, 12, 1, 2],
        "monsoon_months": [6, 7, 8],
        "interests": ["heritage", "photography", "culture", "trekking", "architecture"],
        "trip_types": ["solo", "friends", "couple", "group"],
        "min_budget_per_day_inr": 1900.0,
        "coordinates": {"lat": 15.3350, "lon": 76.4600},
        "highlights": ["Virupaksha Temple", "Vijaya Vittala Stone Chariot", "Matanga Hill Sunrise", "Tungabhadra Coracle Ride"],
        "seasonal_note": "Pleasant winter mornings with mild afternoon sun, optimal for bicycling among stone ruins.",
    },
    {
        "name": "Munnar",
        "state_or_country": "Kerala, India",
        "tagline": "Misty tea capital — sprawling green carpets, mountain peaks, and cool waterfalls",
        "climate": "hill_station",
        "best_months": [9, 10, 11, 12, 1, 2, 3, 4],
        "monsoon_months": [6, 7, 8],
        "interests": ["nature", "tea", "mountains", "scenic", "relaxation", "trekking"],
        "trip_types": ["couple", "family", "solo", "friends"],
        "min_budget_per_day_inr": 2300.0,
        "coordinates": {"lat": 10.0889, "lon": 77.0595},
        "highlights": ["Eravikulam National Park", "Mattupetty Dam & Lake", "Tea Museum & Kolukkumalai", "Attukad Waterfalls"],
        "seasonal_note": "Chilly mountain weather (10-20°C) with rolling mists across tea carpeted hills.",
    },
]


def get_destination_catalog_entry(name: str) -> Optional[Dict[str, Any]]:
    """
    Search destination catalog by exact name or substring matching.
    Handles aliases like 'Coorg' for 'Coorg (Kodagu)' and 'Pondicherry' for 'Pondicherry (Puducherry)'.
    """
    if not name or not name.strip():
        return None
    cleaned = name.strip().lower()

    # 1. Exact match
    for d in DESTINATIONS_DB:
        if d["name"].lower() == cleaned:
            return d

    # 2. Cleaned word match (strip punctuation, e.g. 'Coorg' matches 'Coorg (Kodagu)')
    clean_words = re.findall(r"\b[a-zA-Z]+\b", cleaned)
    for d in DESTINATIONS_DB:
        db_words = re.findall(r"\b[a-zA-Z]+\b", d["name"].lower())
        if any(w in db_words for w in clean_words):
            return d

    # 3. Substring match
    for d in DESTINATIONS_DB:
        if cleaned in d["name"].lower() or d["name"].lower() in cleaned:
            return d

    return None


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

    # If the user already specified a destination, lookup catalog match or create tailored recommendation
    if preferred_destination and preferred_destination.strip():
        pref = preferred_destination.strip()
        matched = get_destination_catalog_entry(pref)
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
            # Fallback for custom destinations not in static catalog:
            # Build authentic tailored highlights based on user interests
            highlights = [
                f"Iconic sights and landmarks of {pref}",
                f"Authentic {pref} regional cuisine and culinary trails",
                f"Cultural heritage and local bazaars in {pref}",
            ]
            if "beaches" in interests:
                highlights.insert(0, f"Scenic coastline and water activities in {pref}")
            elif "mountains" in interests or "trekking" in interests:
                highlights.insert(0, f"Mountain trails and viewpoints in {pref}")
            elif "heritage" in interests or "culture" in interests:
                highlights.insert(0, f"Historic monuments and cultural landmarks of {pref}")

            rec = DestinationRecommendation(
                name=pref,
                tagline=f"Custom destination planned from {origin}",
                highlights=highlights[:4],
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
