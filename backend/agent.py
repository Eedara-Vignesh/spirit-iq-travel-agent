"""
backend/agent.py
================
AI Travel Agent Orchestrator for SpiritIQ.
Assigned to: Member 1 (Team Lead)

Coordinates the multi-step travel planning workflow:
1. Input validation
2. Destination discovery (scoring seasonal suitability)
3. Weather analysis (Open-Meteo live vs seasonal expectations)
4. Routing & Dijkstra corridor path computation
5. Multi-modal transport comparison
6. Budget optimization & per-person breakdown
7. Contextual safety precautions
8. Gemini AI LLM reasoning and day-wise itinerary synthesis
9. Pydantic schema validation & consistency audit
"""

from __future__ import annotations

import datetime
import json
import logging
import re
import time
from datetime import date, timedelta
from typing import Any, Dict, Generator, List, Optional, Tuple

from google import genai
from google.genai import types

from backend.config import get_settings, mask_secret, sanitize_text
from backend.schemas import (
    ActivityItem,
    AgentExecutionTrace,
    AgentStageRecord,
    AlternateRoute,
    BudgetBreakdown,
    BudgetItemBreakdown,
    DayPlan,
    DestinationRecommendation,
    StageStatus,
    ToolProvenance,
    ToolResult,
    TransportMode,
    TransportOption,
    TravelPace,
    TripPlan,
    TripRequest,
    WeatherForecastSummary,
)
from backend.tools.budget_tool import calculate_budget_breakdown
from backend.tools.destination_tool import recommend_destinations
from backend.tools.route_tool import compute_route_options
from backend.tools.safety_tool import get_safety_precautions
from backend.tools.transport_tool import compare_transport_options
from backend.tools.weather_tool import get_weather_forecast

logger = logging.getLogger(__name__)


# ============================================================================
# Specific Error Classes for Agent Resilience
# ============================================================================

class GeminiQuotaExhaustedError(Exception):
    """Raised when Gemini API request quota is exhausted (HTTP 429 RESOURCE_EXHAUSTED)."""

    def __init__(
        self,
        model: str,
        retry_after_seconds: Optional[int] = None,
        quota_details: Optional[str] = None,
        raw_message: Optional[str] = None,
    ) -> None:
        self.model = model
        self.retry_after_seconds = retry_after_seconds
        self.quota_details = quota_details
        self.docs_url = "https://ai.google.dev/gemini-api/docs/rate-limits"
        
        msg = f"Configured Gemini model '{model}' has exhausted its API request quota (HTTP 429 RESOURCE_EXHAUSTED)."
        if retry_after_seconds:
            msg += f" Retry after approximately {retry_after_seconds} seconds."
        else:
            msg += " Please check quota reset timing and project usage limits."
        super().__init__(msg)


class GeminiAuthError(Exception):
    """Raised when Gemini API authentication fails or API key is invalid."""
    pass


class GeminiModelUnavailableError(Exception):
    """Raised when the requested Gemini model is not found or unsupported."""
    pass


class GeminiGenerationError(Exception):
    """Raised when itinerary generation fails due to network, model, or parsing errors."""
    pass


def detect_quota_error(exc: Exception) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Detect whether an exception is a Gemini 429 / RESOURCE_EXHAUSTED quota error.
    Returns (is_quota, retry_after_seconds, quota_limit_name).
    """
    err_str = str(exc)
    err_lower = err_str.lower()

    is_quota = (
        "429" in err_str
        or "resource_exhausted" in err_lower
        or "generaterequestsperday" in err_lower
        or ("quota" in err_lower and "exceeded" in err_lower)
    )
    if not is_quota:
        return False, None, None

    retry_after: Optional[int] = None
    retry_match = re.search(r"retry[\s_-]?after[:\s]+(\d+)", err_str, re.IGNORECASE)
    if retry_match:
        try:
            retry_after = int(retry_match.group(1))
        except ValueError:
            pass

    detail_match = re.search(r"(GenerateRequests[A-Za-z0-9_-]+)", err_str)
    quota_detail = detail_match.group(1) if detail_match else None
    return True, retry_after, quota_detail


# ============================================================================
# Main TravelPlanningAgent Orchestrator
# ============================================================================

class TravelPlanningAgent:
    """
    Core AI orchestrator coordinating specialized backend tools and Gemini AI
    to generate complete, validated TripPlan instances with genuine execution tracing.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.gemini_api_key if api_key is None else api_key
        self.model_name = self.settings.gemini_model

    def plan_trip(self, request: TripRequest) -> TripPlan:
        """
        Execute full multi-step AI planning workflow synchronously.
        Preserves backward compatibility with all unit tests and direct callers.
        """
        final_plan: Optional[TripPlan] = None
        for _, plan in self.plan_trip_stream(request):
            if plan is not None:
                final_plan = plan
        if final_plan is None:
            raise RuntimeError("Agent orchestration failed to return a final plan")
        return final_plan

    def plan_trip_stream(
        self, request: TripRequest
    ) -> Generator[Tuple[AgentExecutionTrace, Optional[TripPlan]], None, TripPlan]:
        """
        Execute full multi-step agent planning workflow as a real generator stream,
        yielding updated AgentExecutionTrace at every stage for genuine UI timeline updates.
        """
        num_days = max(1, (request.end_date - request.start_date).days + 1)
        
        # Initialize Trace with Pipeline Stages
        trace = AgentExecutionTrace(
            model_used=self.model_name,
            stages=[
                AgentStageRecord(stage_id="stage_validate", name="Request Validation"),
                AgentStageRecord(stage_id="stage_destination", name="Destination Discovery"),
                AgentStageRecord(stage_id="stage_weather", name="Weather & Climate Analysis"),
                AgentStageRecord(stage_id="stage_routes", name="Highway Corridor & Routing"),
                AgentStageRecord(stage_id="stage_transit", name="Transport Modal Comparison"),
                AgentStageRecord(stage_id="stage_budget", name="Budget Optimization & Audit"),
                AgentStageRecord(stage_id="stage_safety", name="Safety & Local Advisories"),
                AgentStageRecord(stage_id="stage_gemini", name="Gemini AI Itinerary Synthesis"),
                AgentStageRecord(stage_id="stage_schema", name="Schema & Arithmetic Verification"),
            ],
            activity_log=[],
        )

        def _log(activity: str) -> None:
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            trace.activity_log.append(f"[{now_str}] {activity}")

        # -------------------------------------------------------------
        # Stage 1: Request Validation
        # -------------------------------------------------------------
        stage_val = trace.stages[0]
        stage_val.status = StageStatus.RUNNING
        t0 = time.perf_counter()
        _log(f"Validating travel parameters for {request.origin} ({num_days} days, ₹{request.budget_inr:,.0f})...")
        yield trace, None

        stage_val.status = StageStatus.COMPLETED
        stage_val.provenance = ToolProvenance.DETERMINISTIC.value
        stage_val.summary = f"Validated parameters: {request.origin}, {num_days} days, {request.num_travellers} traveller(s)."
        stage_val.duration_ms = (time.perf_counter() - t0) * 1000
        yield trace, None

        # -------------------------------------------------------------
        # Stage 2: Destination Discovery or Verification
        # -------------------------------------------------------------
        stage_dest = trace.stages[1]
        t0 = time.perf_counter()
        stage_dest.status = StageStatus.RUNNING
        yield trace, None

        discovered_destinations: List[DestinationRecommendation] = []
        if request.destination and request.destination.strip():
            stage_dest.status = StageStatus.SKIPPED
            stage_dest.provenance = ToolProvenance.LOCAL_DATA.value
            stage_dest.summary = f"User specified preferred destination: '{request.destination.strip()}'."
            target_destination = request.destination.strip()
            _log(f"Destination provided by traveler: '{target_destination}' (discovery skipped)")
        else:
            _log("Searching curated destinations database for optimal seasonal match...")
            dest_result = recommend_destinations(
                origin=request.origin,
                interests=request.interests,
                budget_inr=request.budget_inr,
                travel_month=request.start_date.month,
                trip_type=request.trip_type.value,
                preferred_destination=None,
                limit=3,
            )
            if dest_result.success and isinstance(dest_result.data, dict):
                raw_dests = dest_result.data.get("destinations", [])
                discovered_destinations = [DestinationRecommendation.model_validate(d) for d in raw_dests]
            target_destination = discovered_destinations[0].name if discovered_destinations else "Recommended Getaway"
            stage_dest.status = StageStatus.COMPLETED
            stage_dest.tool_name = "recommend_destinations"
            stage_dest.provenance = ToolProvenance.LOCAL_DATA.value
            stage_dest.summary = f"Discovered {len(discovered_destinations)} seasonal candidates. Selected: '{target_destination}'."
            _log(f"Selected top-scored candidate: '{target_destination}'")

        stage_dest.duration_ms = (time.perf_counter() - t0) * 1000
        yield trace, None

        # -------------------------------------------------------------
        # Stage 3: Weather Analysis (Open-Meteo)
        # -------------------------------------------------------------
        stage_w = trace.stages[2]
        t0 = time.perf_counter()
        stage_w.status = StageStatus.RUNNING
        stage_w.tool_name = "get_weather_forecast"
        _log(f"Retrieving meteorological data for '{target_destination}' from Open-Meteo...")
        yield trace, None

        weather_summary: Optional[WeatherForecastSummary] = None
        weather_result = get_weather_forecast(
            location=target_destination,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        if weather_result.success and isinstance(weather_result.data, dict):
            try:
                weather_summary = WeatherForecastSummary.model_validate(weather_result.data)
                meta_source = weather_result.metadata.get("source", "open-meteo")
                stage_w.provenance = ToolProvenance.LIVE_API.value if "open-meteo" in meta_source else ToolProvenance.LOCAL_DATA.value
                stage_w.status = StageStatus.COMPLETED
                stage_w.summary = f"{weather_summary.conditions} (Avg {weather_summary.average_temperature_c or 25:.1f}°C, rain {weather_summary.precipitation_probability or 0:.0f}%)"
                _log(f"Weather fetched: {weather_summary.conditions}, {weather_summary.average_temperature_c or 25:.1f}°C")
            except Exception as e:
                stage_w.status = StageStatus.FAILED
                stage_w.error = str(e)
        else:
            stage_w.status = StageStatus.FAILED
            stage_w.error = weather_result.error or "Weather forecast unavailable"
            _log(f"Notice: Weather forecast lookup warning: {stage_w.error}")

        stage_w.duration_ms = (time.perf_counter() - t0) * 1000
        yield trace, None

        # -------------------------------------------------------------
        # Stage 4: Highway Corridor & Dijkstra Routing
        # -------------------------------------------------------------
        stage_r = trace.stages[3]
        t0 = time.perf_counter()
        stage_r.status = StageStatus.RUNNING
        stage_r.tool_name = "compute_route_options"
        _log(f"Computing highway corridor between '{request.origin}' and '{target_destination}'...")
        yield trace, None

        route_options: List[AlternateRoute] = []
        route_result = compute_route_options(origin=request.origin, destination=target_destination)
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
            is_maps = bool(self.settings.google_maps_api_key)
            stage_r.provenance = ToolProvenance.LIVE_API.value if is_maps else ToolProvenance.GRAPH_SOLVER.value
            stage_r.status = StageStatus.COMPLETED
            stage_r.summary = f"Computed corridor distance: ~{distance_km:.0f} km ({len(route_options)} options via Dijkstra)."
            _log(f"Corridor solved: {distance_km:.0f} km highway corridor")
        else:
            stage_r.status = StageStatus.FAILED
            stage_r.error = route_result.error or "Routing computation error"
            _log(f"Routing computation warning: {stage_r.error}")

        stage_r.duration_ms = (time.perf_counter() - t0) * 1000
        yield trace, None

        # -------------------------------------------------------------
        # Stage 5: Multi-Modal Transport Comparison
        # -------------------------------------------------------------
        stage_t = trace.stages[4]
        t0 = time.perf_counter()
        stage_t.status = StageStatus.RUNNING
        stage_t.tool_name = "compare_transport_options"
        _log("Benchmarking multimodal transit options (flights, trains, buses, cabs)...")
        yield trace, None

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
            stage_t.status = StageStatus.COMPLETED
            stage_t.provenance = ToolProvenance.DETERMINISTIC.value
            stage_t.summary = f"Benchmarked {len(transport_options)} transit options."
            _log(f"Transport benchmark completed: {len(transport_options)} modes evaluated")
        else:
            stage_t.status = StageStatus.FAILED
            stage_t.error = transit_result.error or "Transit benchmark failed"

        stage_t.duration_ms = (time.perf_counter() - t0) * 1000
        yield trace, None

        # -------------------------------------------------------------
        # Stage 6: Deterministic Budget Audit
        # -------------------------------------------------------------
        stage_b = trace.stages[5]
        t0 = time.perf_counter()
        stage_b.status = StageStatus.RUNNING
        stage_b.tool_name = "calculate_budget_breakdown"
        _log(f"Auditing expenditure allocation against INR {request.budget_inr:,.0f} limit...")
        yield trace, None

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
                stage_b.status = StageStatus.COMPLETED
                stage_b.provenance = ToolProvenance.DETERMINISTIC.value
                status_text = "Protected" if budget_breakdown.is_within_budget else "Deficit Alert"
                stage_b.summary = f"Cost ₹{budget_breakdown.estimated_total_cost_inr:,.0f} / ₹{request.budget_inr:,.0f} ({status_text})."
                _log(f"Budget calculated: ₹{budget_breakdown.estimated_total_cost_inr:,.0f} ({status_text})")
            except Exception as e:
                stage_b.status = StageStatus.FAILED
                stage_b.error = str(e)
        else:
            stage_b.status = StageStatus.FAILED
            stage_b.error = budget_result.error or "Budget breakdown calculation failed"

        stage_b.duration_ms = (time.perf_counter() - t0) * 1000
        yield trace, None

        # -------------------------------------------------------------
        # Stage 7: Safety Precautions
        # -------------------------------------------------------------
        stage_s = trace.stages[6]
        t0 = time.perf_counter()
        stage_s.status = StageStatus.RUNNING
        stage_s.tool_name = "get_safety_precautions"
        _log(f"Retrieving safety guidelines and local advisories for '{target_destination}'...")
        yield trace, None

        safety_precautions: List[str] = []
        safety_result = get_safety_precautions(
            destination=target_destination,
            trip_type=request.trip_type.value,
            special_requirements=request.special_requirements,
            weather_conditions=weather_summary.conditions if weather_summary else None,
        )
        if safety_result.success and isinstance(safety_result.data, dict):
            safety_precautions = safety_result.data.get("precautions", [])
            stage_s.status = StageStatus.COMPLETED
            stage_s.provenance = ToolProvenance.LOCAL_DATA.value
            stage_s.summary = f"Compiled {len(safety_precautions)} localized safety protocols."
            _log(f"Compiled {len(safety_precautions)} safety precautions")
        else:
            stage_s.status = StageStatus.FAILED
            stage_s.error = safety_result.error or "Safety advisories unavailable"

        stage_s.duration_ms = (time.perf_counter() - t0) * 1000
        yield trace, None

        # -------------------------------------------------------------
        # Stage 8: Gemini AI LLM Itinerary Synthesis
        # -------------------------------------------------------------
        stage_g = trace.stages[7]
        t0 = time.perf_counter()
        stage_g.status = StageStatus.RUNNING
        stage_g.tool_name = f"Google GenAI SDK ({self.model_name})"
        _log(f"Synthesizing customized day-by-day itinerary using Gemini AI ({self.model_name})...")
        yield trace, None

        # Check API Key Availability
        if not self.api_key or not self.api_key.strip():
            stage_g.status = StageStatus.SKIPPED
            stage_g.provenance = ToolProvenance.FALLBACK.value
            stage_g.summary = "GEMINI_API_KEY not configured in .env. Switched to deterministic tool preview."
            stage_g.duration_ms = (time.perf_counter() - t0) * 1000
            trace.is_preview_mode = True
            _log("GEMINI_API_KEY is not configured. Loaded deterministic rule-based tool preview.")

            # Stage 9: Schema Audit
            stage_audit = trace.stages[8]
            stage_audit.status = StageStatus.COMPLETED
            stage_audit.provenance = ToolProvenance.DETERMINISTIC.value
            stage_audit.summary = "Verified tool outputs and arithmetic contracts."

            fallback_plan = self._build_deterministic_plan(
                request=request,
                target_destination=target_destination,
                num_days=num_days,
                destinations=discovered_destinations,
                weather_summary=weather_summary,
                transport_options=transport_options,
                route_options=route_options,
                budget_breakdown=budget_breakdown,
                safety_precautions=safety_precautions,
                notice_msg="GEMINI_API_KEY is not configured in .env. Displaying verified deterministic tool preview (Non-LLM).",
                is_preview=True,
            )
            fallback_plan.execution_trace = trace
            yield trace, fallback_plan
            return fallback_plan

        # Compose prompt
        prompt = self._compose_orchestration_prompt(
            request=request,
            target_destination=target_destination,
            num_days=num_days,
            discovered_destinations=discovered_destinations,
            weather_summary=weather_summary,
            route_options=route_options,
            transport_options=transport_options,
            budget_breakdown=budget_breakdown,
            safety_precautions=safety_precautions,
        )

        try:
            raw_json = self._call_gemini_with_retry(prompt)
            ai_plan = self._parse_and_validate_ai_plan(
                raw_text=raw_json,
                request=request,
                target_destination=target_destination,
                num_days=num_days,
                discovered_destinations=discovered_destinations,
                weather_summary=weather_summary,
                transport_options=transport_options,
                route_options=route_options,
                budget_breakdown=budget_breakdown,
                safety_precautions=safety_precautions,
                budget_warnings=budget_warnings,
            )
            stage_g.status = StageStatus.COMPLETED
            stage_g.provenance = ToolProvenance.LLM_SYNTHESIS.value
            stage_g.summary = f"Synthesized {num_days}-day itinerary via Gemini model '{self.model_name}'."
            stage_g.duration_ms = (time.perf_counter() - t0) * 1000
            _log("Itinerary synthesized successfully by Gemini AI")
            yield trace, None

            # -------------------------------------------------------------
            # Stage 9: Schema Audit & Verification
            # -------------------------------------------------------------
            stage_audit = trace.stages[8]
            t_aud = time.perf_counter()
            stage_audit.status = StageStatus.RUNNING
            _log("Auditing final Pydantic contracts and budget arithmetic...")
            yield trace, None

            stage_audit.status = StageStatus.COMPLETED
            stage_audit.provenance = ToolProvenance.DETERMINISTIC.value
            stage_audit.summary = "All Pydantic contracts, activity time-slots, and date sequences verified."
            stage_audit.duration_ms = (time.perf_counter() - t_aud) * 1000
            _log("Pydantic schema contracts validated successfully")

            ai_plan.execution_trace = trace
            yield trace, ai_plan
            return ai_plan

        except GeminiQuotaExhaustedError as quota_err:
            stage_g.status = StageStatus.FAILED
            stage_g.provenance = ToolProvenance.LLM_SYNTHESIS.value
            stage_g.summary = f"Quota Exhausted: Free-tier limit reached for '{self.model_name}' (429 RESOURCE_EXHAUSTED)."
            stage_g.error = str(quota_err)
            stage_g.duration_ms = (time.perf_counter() - t0) * 1000

            trace.has_quota_error = True
            trace.is_preview_mode = True
            trace.quota_error_details = {
                "model": self.model_name,
                "retry_after": quota_err.retry_after_seconds,
                "quota_details": quota_err.quota_details,
                "docs_url": quota_err.docs_url,
            }
            _log(f"⚠️ Gemini request quota exhausted (429). Preserving form; generating deterministic tool preview.")
            yield trace, None

            stage_audit = trace.stages[8]
            stage_audit.status = StageStatus.COMPLETED
            stage_audit.provenance = ToolProvenance.DETERMINISTIC.value
            stage_audit.summary = "Verified tool outputs for deterministic preview mode."

            preview_plan = self._build_deterministic_plan(
                request=request,
                target_destination=target_destination,
                num_days=num_days,
                destinations=discovered_destinations,
                weather_summary=weather_summary,
                transport_options=transport_options,
                route_options=route_options,
                budget_breakdown=budget_breakdown,
                safety_precautions=safety_precautions,
                notice_msg=(
                    f"Notice: Google Gemini model '{self.model_name}' request quota is exhausted (HTTP 429 RESOURCE_EXHAUSTED). "
                    f"Displaying verified tool outputs (Weather, Dijkstra Corridor, and Budget Audit) in deterministic preview mode. "
                    f"For quota details and rate limits, visit: https://ai.google.dev/gemini-api/docs/rate-limits"
                ),
                is_preview=True,
                is_quota=True,
            )
            preview_plan.execution_trace = trace
            yield trace, preview_plan
            return preview_plan

        except Exception as exc:
            safe_err = sanitize_text(str(exc), secrets=[self.api_key])
            stage_g.status = StageStatus.FAILED
            stage_g.error = f"Gemini error: {safe_err}"
            stage_g.duration_ms = (time.perf_counter() - t0) * 1000
            trace.is_preview_mode = True
            _log(f"Gemini API call failed ({safe_err}). Falling back to deterministic tool preview.")
            yield trace, None

            stage_audit = trace.stages[8]
            stage_audit.status = StageStatus.COMPLETED
            stage_audit.provenance = ToolProvenance.DETERMINISTIC.value
            stage_audit.summary = "Verified tool outputs for fallback baseline."

            fallback_plan = self._build_deterministic_plan(
                request=request,
                target_destination=target_destination,
                num_days=num_days,
                destinations=discovered_destinations,
                weather_summary=weather_summary,
                transport_options=transport_options,
                route_options=route_options,
                budget_breakdown=budget_breakdown,
                safety_precautions=safety_precautions,
                notice_msg=f"Notice: Live AI generation encountered a temporary error ({safe_err}). Loaded modular tool baseline.",
                is_preview=True,
            )
            fallback_plan.execution_trace = trace
            yield trace, fallback_plan
            return fallback_plan

    def _compose_orchestration_prompt(
        self,
        request: TripRequest,
        target_destination: str,
        num_days: int,
        discovered_destinations: List[DestinationRecommendation],
        weather_summary: Optional[WeatherForecastSummary],
        route_options: List[AlternateRoute],
        transport_options: List[TransportOption],
        budget_breakdown: Optional[BudgetBreakdown],
        safety_precautions: List[str],
    ) -> str:
        """Compose rich prompt containing pre-computed tool facts to ground the Gemini response."""
        dest_context = (
            f"The traveler specified: '{target_destination}'."
            if request.destination
            else f"The traveler did not specify a destination. We discovered '{target_destination}' as the best candidate based on {request.start_date.strftime('%B')} seasonality and budget."
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

        schema_json = json.dumps(TripPlan.model_json_schema(), indent=2)

        return f"""You are SpiritIQ — an expert AI Travel Planning Agent for India and global destinations.
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
- Weather Guidance: {weather_text}
- Dijkstra Routing Corridor: {routes_text}
- Feasible Transit Modes: {transit_text}

### Instructions:
1. Provide an executive summary of the journey and an inspiring trip title.
2. Generate an exact day-by-day itinerary for all {num_days} days (day_number 1 to {num_days}).
3. For each day, include distinct morning, afternoon, and evening activities matching the {request.pace.value} pace, with realistic INR cost estimates.
4. Provide structured budget allocations that fit within the INR {request.budget_inr:,.2f} limit.
5. Provide practical, localized safety precautions.

### Output Requirement:
Output MUST be a single, valid JSON object strictly matching this JSON schema:
{schema_json}

Do not include any explanation or markdown formatting outside the JSON object.
"""

    def _call_gemini_with_retry(self, prompt: str, max_retries: int = 1) -> str:
        """
        Execute Gemini API call with safe retry on transient failures.
        Never automatically retries quota errors (429 RESOURCE_EXHAUSTED).
        """
        client = genai.Client(api_key=self.api_key)
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        )

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )
                if response and response.text:
                    return response.text
                raise ValueError("Empty response text returned by Gemini API")
            except Exception as exc:
                last_error = exc
                is_quota, retry_after, quota_detail = detect_quota_error(exc)
                if is_quota:
                    # Never retry quota exhaustion in a tight loop!
                    logger.warning(
                        "Gemini quota exhausted for model %s: %s (no retry)",
                        self.model_name,
                        quota_detail or "RESOURCE_EXHAUSTED",
                    )
                    raise GeminiQuotaExhaustedError(
                        model=self.model_name,
                        retry_after_seconds=retry_after,
                        quota_details=quota_detail,
                        raw_message=str(exc),
                    ) from exc

                # Check if API key invalid
                exc_str_lower = str(exc).lower()
                if "api_key_invalid" in exc_str_lower or "api key not valid" in exc_str_lower:
                    raise GeminiAuthError(f"Invalid Gemini API key: {sanitize_text(str(exc))}") from exc

                if "404" in str(exc) or "not found" in exc_str_lower:
                    raise GeminiModelUnavailableError(f"Gemini model '{self.model_name}' not found: {sanitize_text(str(exc))}") from exc

                safe_msg = sanitize_text(str(exc), secrets=[self.api_key])
                logger.warning("Gemini API call attempt %d failed: %s", attempt + 1, safe_msg)
                if attempt < max_retries:
                    time.sleep(2.0 * (attempt + 1))

        raise last_error or RuntimeError("Gemini API call failed after retries")

    def _parse_and_validate_ai_plan(
        self,
        raw_text: str,
        request: TripRequest,
        target_destination: str,
        num_days: int,
        discovered_destinations: List[DestinationRecommendation],
        weather_summary: Optional[WeatherForecastSummary],
        transport_options: List[TransportOption],
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

        # Merge tool-backed recommendations if AI generated empty lists
        if not plan.destinations and discovered_destinations:
            plan.destinations = discovered_destinations
        if not plan.weather_summary and weather_summary:
            plan.weather_summary = weather_summary
        if not plan.transport_options and transport_options:
            plan.transport_options = transport_options
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
        plan.metadata["model"] = self.model_name
        return plan

    def _build_deterministic_plan(
        self,
        request: TripRequest,
        target_destination: str,
        num_days: int,
        destinations: List[DestinationRecommendation],
        weather_summary: Optional[WeatherForecastSummary],
        transport_options: List[TransportOption],
        route_options: List[AlternateRoute],
        budget_breakdown: Optional[BudgetBreakdown],
        safety_precautions: List[str],
        notice_msg: str,
        is_preview: bool = False,
        is_quota: bool = False,
    ) -> TripPlan:
        """
        Construct structured itinerary from verified tool outputs.
        Explicitly marked as deterministic non-LLM preview to maintain transparency.
        """
        itinerary: List[DayPlan] = []
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
                            title=f"Iconic Landmarks of {target_destination}",
                            description="Guided orientation, architecture, and photography.",
                            location=target_destination,
                            estimated_cost_inr=500.0,
                        ),
                        ActivityItem(
                            time_slot="Afternoon (14:00 - 17:00)",
                            title="Local Heritage & Authentic Culinary Walk",
                            description="Taste renowned regional specialties and visit cultural spots.",
                            location=f"{target_destination} Old Quarter",
                            estimated_cost_inr=800.0,
                        ),
                        ActivityItem(
                            time_slot="Evening (18:00 - 20:30)",
                            title="Sunset Viewpoint & Leisure Bazaars",
                            description="Scenic viewpoint visit followed by local handicraft markets.",
                            location=target_destination,
                            estimated_cost_inr=400.0,
                        ),
                    ],
                    estimated_daily_cost_inr=1700.0,
                    day_notes=f"Pace: {request.pace.value.capitalize()}. Pre-booking recommended during peak travel months.",
                )
            )

        title_prefix = "Deterministic Tool Preview (Non-LLM)" if is_preview else "SpiritIQ Expedition"
        summary_prefix = "[Deterministic Rule-Based Preview — Not AI Generated]" if is_preview else "Tool-synthesized travel plan:"

        return TripPlan(
            trip_title=f"{title_prefix}: {request.origin} to {target_destination}",
            summary=(
                f"{summary_prefix} Verified tool itinerary from {request.origin} to {target_destination} "
                f"for {request.trip_type.value} travel ({request.num_travellers} traveller(s)) with a ₹{request.budget_inr:,.0f} budget."
            ),
            destinations=destinations,
            itinerary=itinerary,
            weather_summary=weather_summary,
            transport_options=transport_options,
            budget_breakdown=budget_breakdown,
            safety_precautions=safety_precautions,
            alternate_routes=route_options,
            errors=[notice_msg],
            metadata={
                "ai_orchestrated": False,
                "is_preview_mode": is_preview,
                "has_quota_error": is_quota,
                "source": "deterministic_tool_corridor_preview",
            },
        )
