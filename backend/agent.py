"""
backend/agent.py
================
AI Travel Agent Orchestrator for SpiritIQ.
Assigned to: Member 1 (Team Lead)

Coordinates the multi-step travel planning workflow:
1. Input validation & destination discovery / verification
2. Weather analysis (Open-Meteo live vs seasonal expectations)
3. Routing & Dijkstra corridor path computation
4. Multi-modal transport comparison
5. Connected multi-modal journeys (Hubs & feeder transfers)
6. Accommodation & hotel search
7. Budget optimization & per-person breakdown
8. Contextual safety precautions
9. Groq AI LLM reasoning and day-wise itinerary synthesis
10. Pydantic schema validation, destination verification & consistency audit
"""

from __future__ import annotations

import json
import logging
import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from groq import Groq

from backend.config import get_settings, mask_secret, sanitize_text
from backend.schemas import (
    ActivityItem,
    AlternateRoute,
    BookingOrder,
    BudgetBreakdown,
    BudgetItemBreakdown,
    ConnectedJourney,
    DayPlan,
    DestinationRecommendation,
    HotelOption,
    ToolResult,
    TransportMode,
    TransportOption,
    TravelPace,
    TravellerProfile,
    TripPlan,
    TripRequest,
    WeatherForecastSummary,
)
from backend.tools.booking_tool import booking_manager
from backend.tools.budget_tool import calculate_budget_breakdown
from backend.tools.destination_tool import get_destination_catalog_entry, recommend_destinations
from backend.tools.hotel_tool import search_hotels
from backend.tools.hub_tool import generate_connected_journeys
from backend.tools.itinerary_tool import build_daywise_itinerary
from backend.tools.route_tool import compute_route_options
from backend.tools.safety_tool import get_safety_precautions
from backend.tools.transport_tool import compare_transport_options
from backend.tools.weather_tool import get_weather_forecast

logger = logging.getLogger(__name__)


class TravelPlanningAgent:
    """
    Core AI orchestrator coordinating specialized backend tools and Groq AI
    to generate complete, validated TripPlan instances.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.groq_api_key if api_key is None else api_key
        self.model_name = model_name or self.settings.groq_model

    def plan_trip(self, request: TripRequest) -> TripPlan:
        """
        Execute full multi-step AI planning workflow.
        """
        num_days = max(1, (request.end_date - request.start_date).days + 1)

        # -------------------------------------------------------------
        # Step 1: Destination Discovery or Verification
        # -------------------------------------------------------------
        dest_result = recommend_destinations(
            origin=request.origin,
            interests=request.interests,
            budget_inr=request.budget_inr,
            travel_month=request.start_date.month,
            trip_type=request.trip_type.value,
            preferred_destination=request.destination,
            limit=3,
        )
        discovered_destinations: List[DestinationRecommendation] = []
        if dest_result.success and isinstance(dest_result.data, dict):
            raw_dests = dest_result.data.get("destinations", [])
            discovered_destinations = [DestinationRecommendation.model_validate(d) for d in raw_dests]

        # Selected destination for the itinerary
        target_destination = (
            request.destination.strip()
            if request.destination and request.destination.strip()
            else (discovered_destinations[0].name if discovered_destinations else "Recommended Getaway")
        )

        # -------------------------------------------------------------
        # Step 2: Weather Forecast / Guidance
        # -------------------------------------------------------------
        weather_summary: Optional[WeatherForecastSummary] = None
        weather_result = get_weather_forecast(
            location=target_destination,
            start_date=request.start_date,
            end_date=request.end_date,
            coordinates=request.destination_coordinates,
        )
        if weather_result.success and isinstance(weather_result.data, dict):
            try:
                weather_summary = WeatherForecastSummary.model_validate(weather_result.data)
            except Exception:
                pass

        # -------------------------------------------------------------
        # Step 3: Routing & Dijkstra Corridor
        # -------------------------------------------------------------
        route_options: List[AlternateRoute] = []
        route_result = compute_route_options(
            origin=request.origin,
            destination=target_destination,
            origin_coords=request.origin_coordinates,
            dest_coords=request.destination_coordinates,
        )
        distance_km = 350.0
        if route_result.success and isinstance(route_result.data, dict):
            for r in route_result.data.get("routes", []):
                try:
                    ar = AlternateRoute.model_validate(r)
                    route_options.append(ar)
                    if ar.total_distance_km:
                        distance_km = ar.total_distance_km
                except Exception:
                    pass

        # -------------------------------------------------------------
        # Step 4: Multi-Modal Transport Comparison
        # -------------------------------------------------------------
        transport_options: List[TransportOption] = []
        transit_result = compare_transport_options(
            origin=request.origin,
            destination=target_destination,
            distance_km=distance_km,
            preferences=request.transport_preferences,
            num_travellers=request.num_travellers,
        )
        if transit_result.success and isinstance(transit_result.data, dict):
            for t in transit_result.data.get("transport_options", []):
                try:
                    transport_options.append(TransportOption.model_validate(t))
                except Exception:
                    pass

        # -------------------------------------------------------------
        # Step 4b: Connected Multi-Modal Journey Planning (Hubs & Feeder Transfers)
        # -------------------------------------------------------------
        connected_journeys: List[ConnectedJourney] = []
        conn_res = generate_connected_journeys(
            origin=request.origin,
            destination=target_destination,
            num_travellers=request.num_travellers,
            preferences=request.transport_preferences,
        )
        if conn_res.success and isinstance(conn_res.data, list):
            connected_journeys = conn_res.data

        # -------------------------------------------------------------
        # Step 4c: Accommodation & Hotel Search
        # -------------------------------------------------------------
        hotel_recommendations: List[HotelOption] = []
        hotel_res = search_hotels(
            destination=target_destination,
            check_in_date=request.start_date,
            check_out_date=request.end_date,
            num_guests=request.num_travellers,
            num_rooms=request.num_rooms,
            preferred_category=request.hotel_category,
            amenities_required=request.hotel_amenities,
        )
        if hotel_res.success and isinstance(hotel_res.data, list):
            hotel_recommendations = hotel_res.data

        # -------------------------------------------------------------
        # Step 4d: Initialize Active Booking Order
        # -------------------------------------------------------------
        selected_hotel = hotel_recommendations[0] if hotel_recommendations else None
        selected_segments = (
            connected_journeys[0].segments
            if connected_journeys and connected_journeys[0].segments
            else []
        )
        active_order = booking_manager.create_or_get_order(
            trip_title=f"SpiritIQ Expedition: {request.origin} to {target_destination}",
            traveller_profile=TravellerProfile(
                num_adults=request.num_travellers,
                special_notes=request.special_requirements,
            ),
            selected_segments=selected_segments,
            selected_hotel=selected_hotel,
            estimated_activities_inr=1500.0 * num_days,
            estimated_food_inr=1200.0 * num_days * request.num_travellers,
        )

        # -------------------------------------------------------------
        # Step 5: Budget Breakdown & Audit
        # -------------------------------------------------------------
        budget_breakdown: Optional[BudgetBreakdown] = None
        budget_warnings: List[str] = []
        budget_result = calculate_budget_breakdown(
            total_budget_inr=request.budget_inr,
            num_days=num_days,
            num_travellers=request.num_travellers,
            pace=request.pace,
        )
        if budget_result.success and isinstance(budget_result.data, dict):
            try:
                budget_breakdown = BudgetBreakdown.model_validate(budget_result.data)
                deficit_note = budget_result.data.get("deficit_warning")
                if deficit_note:
                    budget_warnings.append(deficit_note)
            except Exception:
                pass

        # -------------------------------------------------------------
        # Step 6: Safety Precautions
        # -------------------------------------------------------------
        safety_precautions: List[str] = []
        safety_result = get_safety_precautions(
            destination=target_destination,
            trip_type=request.trip_type.value,
            special_requirements=request.special_requirements,
            weather_conditions=weather_summary.conditions if weather_summary else None,
        )
        if safety_result.success and isinstance(safety_result.data, dict):
            safety_precautions = safety_result.data.get("precautions", [])

        # -------------------------------------------------------------
        # Step 7: Check Groq API Configuration
        # -------------------------------------------------------------
        if not self.api_key or not self.api_key.strip():
            logger.warning("GROQ_API_KEY is not configured.")
            return self._build_deterministic_plan(
                request=request,
                target_destination=target_destination,
                num_days=num_days,
                destinations=discovered_destinations,
                weather_summary=weather_summary,
                transport_options=transport_options,
                connected_journeys=connected_journeys,
                hotel_recommendations=hotel_recommendations,
                active_booking_order=active_order,
                route_options=route_options,
                budget_breakdown=budget_breakdown,
                safety_precautions=safety_precautions,
                notice_msg="Notice: GROQ_API_KEY is not configured in .env. Showing foundation plan grounded in modular tool outputs.",
            )

        # -------------------------------------------------------------
        # Step 8: Groq AI LLM Orchestration & Day-wise Synthesis
        # -------------------------------------------------------------
        prompt = self._compose_orchestration_prompt(
            request=request,
            target_destination=target_destination,
            num_days=num_days,
            discovered_destinations=discovered_destinations,
            weather_summary=weather_summary,
            route_options=route_options,
            transport_options=transport_options,
            connected_journeys=connected_journeys,
            hotel_recommendations=hotel_recommendations,
            budget_breakdown=budget_breakdown,
            safety_precautions=safety_precautions,
        )

        try:
            raw_json = self._call_groq_with_retry(prompt)
            ai_plan = self._parse_and_validate_ai_plan(
                raw_text=raw_json,
                request=request,
                target_destination=target_destination,
                num_days=num_days,
                discovered_destinations=discovered_destinations,
                weather_summary=weather_summary,
                transport_options=transport_options,
                connected_journeys=connected_journeys,
                hotel_recommendations=hotel_recommendations,
                active_booking_order=active_order,
                route_options=route_options,
                budget_breakdown=budget_breakdown,
                safety_precautions=safety_precautions,
                budget_warnings=budget_warnings,
            )
            return ai_plan
        except Exception as exc:
            safe_err = sanitize_text(str(exc), secrets=[self.api_key])
            logger.error("Groq AI planning call failed: %s", safe_err)
            return self._build_deterministic_plan(
                request=request,
                target_destination=target_destination,
                num_days=num_days,
                destinations=discovered_destinations,
                weather_summary=weather_summary,
                transport_options=transport_options,
                connected_journeys=connected_journeys,
                hotel_recommendations=hotel_recommendations,
                active_booking_order=active_order,
                route_options=route_options,
                budget_breakdown=budget_breakdown,
                safety_precautions=safety_precautions,
                notice_msg=f"Notice: Live Groq AI generation encountered a temporary error ({safe_err}). Loaded modular tool baseline.",
            )

    def _compose_orchestration_prompt(
        self,
        request: TripRequest,
        target_destination: str,
        num_days: int,
        discovered_destinations: List[DestinationRecommendation],
        weather_summary: Optional[WeatherForecastSummary],
        route_options: List[AlternateRoute],
        transport_options: List[TransportOption],
        connected_journeys: List[ConnectedJourney],
        hotel_recommendations: List[HotelOption],
        budget_breakdown: Optional[BudgetBreakdown],
        safety_precautions: List[str],
    ) -> str:
        """Compose rich prompt containing verified destination facts to ground the Groq response."""
        # Retrieve verified destination highlights
        highlights = []
        state_info = ""
        if discovered_destinations and discovered_destinations[0].highlights:
            highlights = discovered_destinations[0].highlights
            state_info = discovered_destinations[0].state_or_country or ""
        elif get_destination_catalog_entry(target_destination):
            cat_entry = get_destination_catalog_entry(target_destination)
            if cat_entry:
                highlights = cat_entry.get("highlights", [])
                state_info = cat_entry.get("state_or_country", "")

        dest_context = (
            f"The traveler explicitly specified: '{target_destination}' ({state_info})."
            if request.destination
            else f"Automated discovery recommended '{target_destination}' ({state_info}) based on {request.start_date.strftime('%B')} seasonality and budget."
        )

        highlights_text = (
            f"Key verified landmarks & highlights to incorporate: {', '.join(highlights)}"
            if highlights
            else f"Explore authentic cultural, historical, and scenic points of interest located specifically in {target_destination}."
        )

        weather_text = (
            f"{weather_summary.conditions} (Packing tips: {', '.join(weather_summary.packing_recommendations)})"
            if weather_summary
            else "Seasonal temperate conditions."
        )

        transit_text = (
            "; ".join(f"{t.mode.value}: {t.provider_or_route} (~₹{t.estimated_cost_inr:,.0f})" for t in transport_options[:3])
            if transport_options
            else "Standard intercity transit."
        )

        routes_text = (
            "; ".join(f"{r.route_name} ({r.total_distance_km} km)" for r in route_options[:2])
            if route_options
            else "Direct highway corridor."
        )

        connected_text = ""
        if connected_journeys:
            sample_cj = connected_journeys[0]
            legs = " -> ".join(s.leg_title for s in sample_cj.segments)
            connected_text = f"Primary Multimodal Journey ({sample_cj.route_type}): {legs} (Est. Duration: {sample_cj.total_duration_hours:.1f} hrs, ₹{sample_cj.total_transit_cost_inr:,.0f})"

        hotel_text = ""
        if hotel_recommendations:
            top_h = hotel_recommendations[:2]
            hotel_text = "; ".join(f"{h.name} ({h.category.value.capitalize()}, ₹{h.price_per_night_inr:,.0f}/night)" for h in top_h)

        schema_template = """{
  "trip_title": "Title of trip",
  "summary": "Trip overview",
  "destinations": [
    {
      "name": "Destination Name",
      "state_or_country": "State/Country",
      "tagline": "Tagline",
      "highlights": ["Highlight 1", "Highlight 2"],
      "best_season": "Best season",
      "estimated_cost_inr": 15000.0
    }
  ],
  "itinerary": [
    {
      "day_number": 1,
      "date": "YYYY-MM-DD",
      "theme_or_title": "Day Theme",
      "activities": [
        {
          "time_slot": "Morning / Afternoon / Evening",
          "title": "Activity name",
          "description": "Details",
          "location": "Location",
          "estimated_cost_inr": 500.0
        }
      ],
      "estimated_daily_cost_inr": 1500.0
    }
  ],
  "budget_breakdown": {
    "total_budget_inr": 0.0,
    "estimated_total_cost_inr": 0.0,
    "remaining_buffer_inr": 0.0,
    "is_within_budget": true,
    "categories": [
      {"category": "Accommodation", "allocated_amount_inr": 0.0, "percentage_of_total": 50.0},
      {"category": "Activities & Food", "allocated_amount_inr": 0.0, "percentage_of_total": 50.0}
    ]
  },
  "safety_precautions": ["Precautions"]
}"""

        return f"""You are SpiritIQ — an expert AI Travel Planning Agent powered by Groq.
Generate a structured, personalized, realistic travel plan based on the following verified facts:

### User Input:
- Origin: {request.origin}
- Target Destination: {target_destination}
- Dates: {request.start_date.isoformat()} to {request.end_date.isoformat()} ({num_days} full days)
- Group Type: {request.trip_type.value.capitalize()} ({request.num_travellers} traveller(s))
- Total Budget: INR {request.budget_inr:,.2f}
- Pace: {request.pace.value.capitalize()}
- Interests: {', '.join(request.interests) if request.interests else 'Sightseeing, local cuisine, culture'}
- Special Requirements: {request.special_requirements or 'None'}

### Verified Grounding from Specialized Tools:
- Destination Context: {dest_context}
- {highlights_text}
- Weather Guidance: {weather_text}
- Dijkstra Routing Corridor: {routes_text}
- Feasible Transit Modes: {transit_text}
- Connected Multi-Modal Feeder Transfers: {connected_text or 'Direct regional access'}
- Accommodation Candidates: {hotel_text or 'Standard local stays'}

### Instructions:
1. Provide an inspiring trip title and executive summary specifically about traveling to {target_destination}.
2. Generate an exact day-by-day itinerary for all {num_days} days (day_number 1 to {num_days}).
3. All activities must be physically located in {target_destination} and immediate surroundings. Do NOT generate activities from other destinations (e.g. do not suggest beaches in mountain areas or forts in coastal towns unless they genuinely exist there).
4. For each day, include distinct morning, afternoon, and evening activities matching the {request.pace.value} pace, with realistic INR cost estimates.
5. Provide structured budget allocations that fit within the INR {request.budget_inr:,.2f} limit.
6. Provide practical, localized safety precautions relevant to {target_destination}.

### Output Requirement:
Output MUST be a single, valid JSON object matching this structure:
{schema_template}

Do not include any explanation or markdown formatting outside the JSON object.
"""

    def _call_groq_with_retry(self, prompt: str, max_retries: int = 1) -> str:
        """Execute Groq API call with safe retry on transient failures."""
        client = Groq(api_key=self.api_key)

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are SpiritIQ — an expert AI Travel Planning Agent. "
                                "Synthesize structured, personalized, realistic travel plans. "
                                "Output MUST be a single, valid JSON object strictly matching the user-requested schema without markdown wrapping."
                            ),
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=2048,
                )

                if response and response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content
                raise ValueError("Empty response text returned by Groq API")
            except Exception as exc:
                last_error = exc
                safe_msg = sanitize_text(str(exc), secrets=[self.api_key])
                logger.warning("Groq API call attempt %d failed: %s", attempt + 1, safe_msg)
                if attempt < max_retries:
                    time.sleep(1.5 * (attempt + 1))

        raise last_error or RuntimeError("Groq API call failed after retries")

    def _parse_and_validate_ai_plan(
        self,
        raw_text: str,
        request: TripRequest,
        target_destination: str,
        num_days: int,
        discovered_destinations: List[DestinationRecommendation],
        weather_summary: Optional[WeatherForecastSummary],
        transport_options: List[TransportOption],
        connected_journeys: List[ConnectedJourney],
        hotel_recommendations: List[HotelOption],
        active_booking_order: Optional[BookingOrder],
        route_options: List[AlternateRoute],
        budget_breakdown: Optional[BudgetBreakdown],
        safety_precautions: List[str],
        budget_warnings: List[str],
    ) -> TripPlan:
        """Parse raw JSON and guarantee integrity through Pydantic models."""
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        data = json.loads(clean_text)
        plan = TripPlan.model_validate(data)

        # Verify destination alignment
        if not plan.destinations:
            plan.destinations = discovered_destinations
        elif plan.destinations and plan.destinations[0].name.lower() != target_destination.lower():
            # Align top destination with user's verified target
            if discovered_destinations:
                plan.destinations[0] = discovered_destinations[0]

        # Audit itinerary length and dates
        if len(plan.itinerary) != num_days or any(plan.itinerary[i].date != (request.start_date + timedelta(days=i)) for i in range(len(plan.itinerary))):
            # Re-index dates to strictly match requested trip timeframe
            repaired_itinerary: List[DayPlan] = []
            for i in range(num_days):
                day_date = request.start_date + timedelta(days=i)
                if i < len(plan.itinerary):
                    dp = plan.itinerary[i]
                    dp.day_number = i + 1
                    dp.date = day_date
                    repaired_itinerary.append(dp)
                else:
                    # Fill missing day using destination-grounded activities
                    fb_res = build_daywise_itinerary(
                        destination=target_destination,
                        start_date=day_date,
                        end_date=day_date,
                        interests=request.interests,
                        pace=request.pace,
                    )
                    if fb_res.success and isinstance(fb_res.data, dict) and fb_res.data.get("itinerary"):
                        new_dp = DayPlan.model_validate(fb_res.data["itinerary"][0])
                        new_dp.day_number = i + 1
                        new_dp.date = day_date
                        repaired_itinerary.append(new_dp)
            plan.itinerary = repaired_itinerary

        # Merge tool-backed recommendations if AI generated empty lists
        if not plan.weather_summary and weather_summary:
            plan.weather_summary = weather_summary
        if not plan.transport_options and transport_options:
            plan.transport_options = transport_options
        if not plan.connected_journeys and connected_journeys:
            plan.connected_journeys = connected_journeys
        if not plan.hotel_recommendations and hotel_recommendations:
            plan.hotel_recommendations = hotel_recommendations
        if not plan.active_booking_order and active_booking_order:
            plan.active_booking_order = active_booking_order
        if not plan.alternate_routes and route_options:
            plan.alternate_routes = route_options
        if not plan.budget_breakdown and budget_breakdown:
            plan.budget_breakdown = budget_breakdown
        if not plan.safety_precautions and safety_precautions:
            plan.safety_precautions = safety_precautions

        # Append any budget alerts
        for bw in budget_warnings:
            if bw not in plan.errors:
                plan.errors.append(bw)

        plan.metadata["ai_orchestrated"] = True
        plan.metadata["is_fallback"] = False
        plan.metadata["model"] = self.model_name
        plan.metadata["llm_provider"] = "groq"
        return plan

    def _build_deterministic_plan(
        self,
        request: TripRequest,
        target_destination: str,
        num_days: int,
        destinations: List[DestinationRecommendation],
        weather_summary: Optional[WeatherForecastSummary],
        transport_options: List[TransportOption],
        connected_journeys: List[ConnectedJourney],
        hotel_recommendations: List[HotelOption],
        active_booking_order: Optional[BookingOrder],
        route_options: List[AlternateRoute],
        budget_breakdown: Optional[BudgetBreakdown],
        safety_precautions: List[str],
        notice_msg: str,
    ) -> TripPlan:
        """
        Construct full structured itinerary grounded in destination-specific intelligence
        without requiring live Groq AI generation.
        """
        itinerary_res = build_daywise_itinerary(
            destination=target_destination,
            start_date=request.start_date,
            end_date=request.end_date,
            interests=request.interests,
            pace=request.pace,
        )

        itinerary: List[DayPlan] = []
        if itinerary_res.success and isinstance(itinerary_res.data, dict):
            raw_itinerary = itinerary_res.data.get("itinerary", [])
            itinerary = [DayPlan.model_validate(dp) for dp in raw_itinerary]

        # Fallback if itinerary tool returned empty
        if not itinerary:
            for i in range(1, num_days + 1):
                day_date = request.start_date + timedelta(days=i - 1)
                itinerary.append(
                    DayPlan(
                        day_number=i,
                        date=day_date,
                        theme_or_title=f"Day {i}: Exploring {target_destination}",
                        activities=[
                            ActivityItem(
                                time_slot="Morning (09:00 - 12:30)",
                                title=f"Signature Landmarks of {target_destination}",
                                description=f"Guided morning exploration of prominent cultural sights in {target_destination}.",
                                location=target_destination,
                                estimated_cost_inr=500.0,
                            ),
                            ActivityItem(
                                time_slot="Afternoon (14:00 - 17:00)",
                                title=f"{target_destination} Cultural & Gastronomy Walk",
                                description=f"Experience regional culinary specialties and historic quarter streets of {target_destination}.",
                                location=f"{target_destination} District",
                                estimated_cost_inr=750.0,
                            ),
                            ActivityItem(
                                time_slot="Evening (18:00 - 20:30)",
                                title=f"{target_destination} Sunset Point & Bazaars",
                                description=f"Sunset views and artisanal craft shopping across {target_destination}.",
                                location=target_destination,
                                estimated_cost_inr=400.0,
                            ),
                        ],
                        estimated_daily_cost_inr=1650.0,
                        day_notes=f"Pace: {request.pace.value.capitalize()}. Pre-booking recommended during peak travel months.",
                    )
                )

        return TripPlan(
            trip_title=f"SpiritIQ Expedition: {request.origin} to {target_destination}",
            summary=(
                f"Personalized {num_days}-day itinerary from {request.origin} to {target_destination} "
                f"tailored for {request.trip_type.value} travel ({request.num_travellers} traveller(s)) with a ₹{request.budget_inr:,.0f} budget."
            ),
            destinations=destinations,
            itinerary=itinerary,
            weather_summary=weather_summary,
            transport_options=transport_options,
            connected_journeys=connected_journeys,
            hotel_recommendations=hotel_recommendations,
            active_booking_order=active_booking_order,
            budget_breakdown=budget_breakdown,
            safety_precautions=safety_precautions,
            alternate_routes=route_options,
            errors=[notice_msg],
            metadata={
                "ai_orchestrated": False,
                "is_fallback": True,
                "source": "curated_destination_synthesis",
                "model": self.model_name,
                "llm_provider": "groq",
            },
        )
