"""
backend/schemas.py
==================
Pydantic data models for SpiritIQ AI Travel Planning Agent.
Defines strict data contracts between Frontend, Backend Services, and Gemini AI Agent.
"""

from __future__ import annotations

import datetime
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Enums
# ============================================================================

class TripType(str, Enum):
    """Supported trip composition types."""
    SOLO = "solo"
    COUPLE = "couple"
    FAMILY = "family"
    FRIENDS = "friends"
    GROUP = "group"


class TravelPace(str, Enum):
    """Desired trip velocity / intensity."""
    RELAXED = "relaxed"
    BALANCED = "balanced"
    PACKED = "packed"


class TransportMode(str, Enum):
    """Modes of travel supported by routes and transport modules."""
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"
    CAB = "cab"
    SELF_DRIVE = "self_drive"
    ANY = "any"


class StageStatus(str, Enum):
    """Execution status for an individual agent pipeline stage."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class ToolProvenance(str, Enum):
    """Provenance/source label for retrieved or calculated travel data."""
    LIVE_API = "Live External API"
    GRAPH_SOLVER = "Dijkstra Graph Algorithm"
    DETERMINISTIC = "Deterministic Rule-Based"
    LOCAL_DATA = "Curated Reference Database"
    LLM_SYNTHESIS = "Gemini LLM Orchestrator"
    FALLBACK = "Safe Fallback / Heuristic"


# ============================================================================
# TripRequest Model
# ============================================================================

class TripRequest(BaseModel):
    """
    Input model submitted by user / frontend form.
    Captures complete requirements needed for AI agent and backend tools to plan a trip.
    """
    origin: str = Field(
        ...,
        description="Origin city or current location (e.g., 'Bengaluru', 'Delhi')",
        min_length=2,
    )
    destination: Optional[str] = Field(
        default=None,
        description="Optional preferred destination (e.g., 'Goa'). If None, agent will discover/recommend.",
    )
    start_date: date = Field(
        ...,
        description="Trip departure date (YYYY-MM-DD)",
    )
    end_date: date = Field(
        ...,
        description="Trip return/conclusion date (YYYY-MM-DD)",
    )
    trip_type: TripType = Field(
        default=TripType.SOLO,
        description="Trip dynamic: solo, couple, family, friends, group",
    )
    num_travellers: int = Field(
        default=1,
        gt=0,
        description="Total number of travellers (must be at least 1)",
    )
    special_requirements: Optional[str] = Field(
        default=None,
        description="Dietary, accessibility, elderly, or child-friendly requirements",
    )
    age_groups: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional age groups participating, e.g. ['adults', 'children', 'infants', 'seniors']",
    )
    budget_inr: float = Field(
        ...,
        gt=0,
        description="Total budget for the entire trip in Indian Rupees (INR)",
    )
    interests: List[str] = Field(
        default_factory=list,
        description="List of traveler interests, e.g. ['beaches', 'trekking', 'food', 'temples', 'wildlife']",
    )
    pace: TravelPace = Field(
        default=TravelPace.BALANCED,
        description="Pace of the trip: relaxed, balanced, or packed",
    )
    transport_preferences: List[TransportMode] = Field(
        default_factory=lambda: [TransportMode.ANY],
        description="Preferred transport modes (flight, train, bus, cab, self_drive, any)",
    )
    return_journey_preference: Optional[str] = Field(
        default=None,
        description="Special return journey preference (e.g., 'scenic route', 'overnight train', 'direct flight')",
    )
    is_flexible_dates: bool = Field(
        default=False,
        description="Whether traveler can adjust dates by a few days",
    )
    date_flexibility_days: int = Field(
        default=0,
        ge=0,
        description="Flexibility range in days (e.g., +/- 2 days)",
    )

    @field_validator("origin", "destination")
    @classmethod
    def clean_string_fields(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Location string cannot be empty or whitespace only")
            return cleaned
        return None

    @field_validator("budget_inr")
    @classmethod
    def validate_positive_budget(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Budget must be a positive number greater than 0 INR")
        return round(v, 2)

    @model_validator(mode="after")
    def validate_dates(self) -> "TripRequest":
        if self.end_date < self.start_date:
            raise ValueError(
                f"end_date ({self.end_date}) cannot be before start_date ({self.start_date})"
            )
        if not self.is_flexible_dates and self.date_flexibility_days > 0:
            # Normalize: if days are specified, mark flexibility as True
            self.is_flexible_dates = True
        return self


# ============================================================================
# ToolResult Model
# ============================================================================

class ToolResult(BaseModel):
    """
    Standardized result contract returned by all backend tools.
    Provides predictable response handling for agent orchestration.
    """
    success: bool = Field(
        ...,
        description="Whether the tool execution succeeded without critical errors",
    )
    data: Optional[Any] = Field(
        default=None,
        description="Payload returned by the tool (structured dict, list, or primitive)",
    )
    error: Optional[str] = Field(
        default=None,
        description="Human-readable error message if tool failed",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnostic metadata, execution timing, API source, or status tags",
    )

    @classmethod
    def ok(cls, data: Any = None, metadata: Optional[Dict[str, Any]] = None) -> "ToolResult":
        """Factory for successful tool execution."""
        return cls(
            success=True,
            data=data,
            error=None,
            metadata=metadata or {},
        )

    @classmethod
    def fail(cls, error: str, metadata: Optional[Dict[str, Any]] = None) -> "ToolResult":
        """Factory for failed tool execution."""
        return cls(
            success=False,
            data=None,
            error=error,
            metadata=metadata or {},
        )


# ============================================================================
# TripPlan & Component Models
# ============================================================================

class DestinationRecommendation(BaseModel):
    """Recommended destination details."""
    name: str = Field(..., description="Destination city/region name")
    state_or_country: Optional[str] = Field(default=None, description="State or country name")
    tagline: Optional[str] = Field(default=None, description="Short compelling tagline")
    highlights: List[str] = Field(default_factory=list, description="Top attraction highlights")
    best_season: Optional[str] = Field(default=None, description="Ideal season/months to visit")
    estimated_cost_inr: Optional[float] = Field(default=None, description="Estimated total cost")
    image_url: Optional[str] = Field(default=None, description="Photo or illustration URL")


class ActivityItem(BaseModel):
    """Specific activity within a day's schedule."""
    time_slot: str = Field(..., description="e.g. 'Morning (09:00 - 11:30)', 'Afternoon', 'Evening'")
    title: str = Field(..., description="Activity title")
    description: Optional[str] = Field(default=None, description="Activity details and context")
    location: Optional[str] = Field(default=None, description="Place or venue name")
    estimated_cost_inr: float = Field(default=0.0, ge=0, description="Estimated activity cost")
    booking_required: bool = Field(default=False, description="Whether advance booking is needed")
    booking_url: Optional[str] = Field(default=None, description="Direct URL or booking link")


class DayPlan(BaseModel):
    """Itinerary for a single day."""
    day_number: int = Field(..., gt=0, description="Sequential day number (1, 2, 3...)")
    date: datetime.date | None = Field(default=None, description="Calendar date of this day")
    theme_or_title: str = Field(..., description="Focus for the day, e.g. 'Heritage Walk & Local Cuisine'")
    activities: List[ActivityItem] = Field(default_factory=list, description="Ordered activities")
    overnight_location: Optional[str] = Field(default=None, description="Hotel/area for overnight stay")
    estimated_daily_cost_inr: float = Field(default=0.0, ge=0, description="Estimated daily sum in INR")
    day_notes: Optional[str] = Field(default=None, description="Helpful tips for this day")


class WeatherForecastSummary(BaseModel):
    """Weather forecast summary for the destination."""
    location: str = Field(..., description="Location name")
    average_temperature_c: Optional[float] = Field(default=None, description="Average temperature in Celsius")
    conditions: Optional[str] = Field(default=None, description="Summary (e.g. 'Partly Cloudy, pleasant')")
    precipitation_probability: Optional[float] = Field(default=None, description="Chance of rain (0-100%)")
    packing_recommendations: List[str] = Field(default_factory=list, description="Gear and clothing advice")
    advisories: List[str] = Field(default_factory=list, description="Weather warnings or advisories")


class TransportOption(BaseModel):
    """Transportation option between origin and destination or day transit."""
    mode: TransportMode = Field(..., description="Transport mode")
    provider_or_route: Optional[str] = Field(default=None, description="Flight number, Train name, or Operator")
    departure_point: str = Field(..., description="Origin hub / station / airport")
    arrival_point: str = Field(..., description="Destination hub / station / airport")
    duration_hours: Optional[float] = Field(default=None, ge=0, description="Travel duration in hours")
    estimated_cost_inr: float = Field(default=0.0, ge=0, description="Cost per person or total")
    booking_url: Optional[str] = Field(default=None, description="Booking reference link")
    is_recommended: bool = Field(default=False, description="Flagged by routing engine as best option")


class BudgetItemBreakdown(BaseModel):
    """Individual line item in budget breakdown."""
    category: str = Field(..., description="e.g. 'Accommodation', 'Transport', 'Food & Dining', 'Activities', 'Buffer'")
    allocated_amount_inr: float = Field(..., ge=0, description="Budget amount in INR")
    percentage_of_total: Optional[float] = Field(default=None, description="Percentage of total budget")
    notes: Optional[str] = Field(default=None, description="Explanation of calculation")


class BudgetBreakdown(BaseModel):
    """Comprehensive budget breakdown."""
    total_budget_inr: float = Field(..., gt=0, description="User's initial budget in INR")
    estimated_total_cost_inr: float = Field(default=0.0, ge=0, description="Computed total trip cost")
    remaining_buffer_inr: float = Field(default=0.0, description="Positive buffer or negative deficit")
    is_within_budget: bool = Field(default=True, description="True if estimated total <= budget")
    categories: List[BudgetItemBreakdown] = Field(default_factory=list, description="Detailed category splits")


class AlternateRoute(BaseModel):
    """Alternate route calculated via Dijkstra or Google Routes."""
    route_name: str = Field(..., description="e.g. 'Scenic Coastal Highway', 'Express Tollway'")
    via_waypoints: List[str] = Field(default_factory=list, description="Stopovers along this route")
    total_distance_km: Optional[float] = Field(default=None, ge=0, description="Distance in kilometres")
    estimated_duration_hours: Optional[float] = Field(default=None, ge=0, description="Duration in hours")
    highlights: List[str] = Field(default_factory=list, description="Scenic or historical stops")
    algorithm_notes: Optional[str] = Field(default=None, description="e.g. 'Shortest path via Dijkstra graph'")


class BookingLink(BaseModel):
    """Direct booking or reservation link."""
    title: str = Field(..., description="Resource name, e.g. 'Taj Exotica Resort Booking'")
    category: str = Field(..., description="Category: 'stay', 'flight', 'train', 'activity'")
    url: str = Field(..., description="Direct HTTPS link")
    description: Optional[str] = Field(default=None, description="Context or promo details")


class AgentStageRecord(BaseModel):
    """Execution status and audit record for an individual agent workflow stage."""
    stage_id: str = Field(..., description="Unique machine identifier for the stage")
    name: str = Field(..., description="Human-readable stage title")
    status: StageStatus = Field(default=StageStatus.PENDING, description="Execution status")
    tool_name: Optional[str] = Field(default=None, description="Internal tool or API invoked")
    provenance: Optional[str] = Field(default=None, description="Data origin (Live API, Dijkstra, Local DB)")
    summary: Optional[str] = Field(default=None, description="Concise summary of findings or results")
    error: Optional[str] = Field(default=None, description="Non-fatal warning or error details")
    duration_ms: Optional[float] = Field(default=None, description="Stage execution time in milliseconds")


class AgentExecutionTrace(BaseModel):
    """Real-time trace capturing end-to-end multi-tool agent orchestration."""
    stages: List[AgentStageRecord] = Field(default_factory=list, description="Ordered pipeline stage records")
    activity_log: List[str] = Field(default_factory=list, description="Live chronological activity log")
    has_quota_error: bool = Field(default=False, description="Whether Gemini model quota was exhausted")
    is_preview_mode: bool = Field(default=False, description="True if operating in deterministic non-LLM preview")
    model_used: Optional[str] = Field(default=None, description="Configured Gemini model identifier")
    quota_error_details: Optional[Dict[str, Any]] = Field(default=None, description="Sanitized quota metadata")


class TripPlan(BaseModel):
    """
    Master Trip Plan assembled by the Agent Orchestrator.
    Consumes outputs from all tools (weather, routes, Dijkstra, budget, places, itinerary).
    """
    trip_title: str = Field(
        default="Personalized SpiritIQ Itinerary",
        description="Catchy title for the trip",
    )
    summary: Optional[str] = Field(
        default=None,
        description="Executive summary of the trip generated by AI agent",
    )
    destinations: List[DestinationRecommendation] = Field(
        default_factory=list,
        description="Recommended destination(s) with highlights",
    )
    itinerary: List[DayPlan] = Field(
        default_factory=list,
        description="Day-by-day travel plan and activities",
    )
    weather_summary: Optional[WeatherForecastSummary] = Field(
        default=None,
        description="Weather conditions and packing tips",
    )
    transport_options: List[TransportOption] = Field(
        default_factory=list,
        description="Available transit options",
    )
    budget_breakdown: Optional[BudgetBreakdown] = Field(
        default=None,
        description="Detailed expenditure breakdown in INR",
    )
    safety_precautions: List[str] = Field(
        default_factory=list,
        description="Curated safety and local advisories",
    )
    alternate_routes: List[AlternateRoute] = Field(
        default_factory=list,
        description="Shortest/alternative paths calculated via Dijkstra or Maps",
    )
    booking_links: List[BookingLink] = Field(
        default_factory=list,
        description="Direct booking and reservation links",
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings or tool failure notices",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent execution metadata, run ID, and timestamps",
    )
    execution_trace: Optional[AgentExecutionTrace] = Field(
        default=None,
        description="Detailed trace of real backend tool execution and provenance",
    )
