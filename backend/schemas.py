"""
backend/schemas.py
==================
Pydantic data models for SpiritIQ AI Travel Planning Agent.
Defines strict data contracts between Frontend, Backend Services, and Groq AI Agent.
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


class HotelCategory(str, Enum):
    """Hotel categories supported by accommodation discovery."""
    BUDGET = "budget"
    BOUTIQUE = "boutique"
    LUXURY = "luxury"
    RESORT = "resort"
    HOMESTAY = "homestay"
    ANY = "any"


class BookingStatus(str, Enum):
    """Explicit state management for transport and hotel reservations."""
    DRAFT = "draft"
    SEARCHING = "searching"
    OPTIONS_AVAILABLE = "options_available"
    SELECTION_MADE = "selection_made"
    AWAITING_USER_REVIEW = "awaiting_user_review"
    AWAITING_USER_APPROVAL = "awaiting_user_approval"
    REDIRECTED_TO_PROVIDER = "redirected_to_provider"
    PENDING_PROVIDER_CONFIRMATION = "pending_provider_confirmation"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
    hotel_required: bool = Field(
        default=True,
        description="Whether hotel accommodation is requested",
    )
    hotel_category: Optional[HotelCategory] = Field(
        default=None,
        description="Preferred hotel category (budget, boutique, luxury, resort, homestay)",
    )
    num_rooms: int = Field(
        default=1,
        ge=1,
        description="Number of hotel rooms needed",
    )
    hotel_amenities: List[str] = Field(
        default_factory=list,
        description="Desired amenities e.g. ['Wi-Fi', 'Swimming Pool', 'Breakfast Included']",
    )
    origin_coordinates: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional GPS coordinates for journey origin {'lat': float, 'lon': float}",
    )
    destination_coordinates: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional GPS coordinates for destination {'lat': float, 'lon': float}",
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
    polyline: Optional[str] = Field(default=None, description="Encoded routing polyline for map representation")
    source: Optional[str] = Field(default=None, description="Route origin engine: 'google_routes' or 'dijkstra_graph'")


class BookingLink(BaseModel):
    """Direct booking or reservation link."""
    title: str = Field(..., description="Resource name, e.g. 'Taj Exotica Resort Booking'")
    category: str = Field(..., description="Category: 'stay', 'flight', 'train', 'activity'")
    url: str = Field(..., description="Direct HTTPS link")
    description: Optional[str] = Field(default=None, description="Context or promo details")


class HotelOption(BaseModel):
    """Hotel or accommodation option."""
    id: str = Field(..., description="Unique identifier for the property")
    name: str = Field(..., description="Hotel property name")
    location: str = Field(..., description="City or specific neighborhood")
    destination: str = Field(..., description="Parent destination")
    category: HotelCategory = Field(default=HotelCategory.BOUTIQUE, description="Property category")
    rating: float = Field(default=4.5, ge=0.0, le=5.0, description="Star rating or review score (0-5)")
    price_per_night_inr: float = Field(..., ge=0, description="Rate per night in INR")
    total_stay_cost_inr: float = Field(..., ge=0, description="Total stay cost for all nights")
    room_type: str = Field(default="Standard Deluxe Room", description="Room classification")
    guest_capacity: int = Field(default=2, ge=1, description="Max guest occupancy")
    amenities: List[str] = Field(default_factory=list, description="Key amenities")
    cancellation_policy: str = Field(default="Free cancellation up to 48 hours prior to check-in", description="Cancellation terms")
    image_url: Optional[str] = Field(default=None, description="Property photo URL")
    booking_url: str = Field(..., description="Official provider reservation link")
    provider: str = Field(default="Booking.com Partner", description="Booking service name")
    is_verified_partner: bool = Field(default=True, description="Whether partner listing is verified")
    is_selected: bool = Field(default=False, description="User selection flag")


class JourneySegment(BaseModel):
    """Single leg of a connected multimodal journey (e.g. Origin -> Hub, Hub -> Hub, Hub -> Hotel)."""
    segment_id: str = Field(..., description="Unique segment identifier")
    leg_number: int = Field(..., ge=1, description="Sequential leg index (1, 2, 3...)")
    leg_title: str = Field(..., description="Description e.g. 'Road Transfer: Narasaraopeta to Vijayawada Hub'")
    origin: str = Field(..., description="Departure point / station / airport")
    destination: str = Field(..., description="Arrival point / hub")
    mode: TransportMode = Field(..., description="Transport mode")
    provider: str = Field(..., description="Carrier, airline, railway line, or cab service")
    departure_time: Optional[str] = Field(default=None, description="Scheduled departure time e.g. '08:30'")
    arrival_time: Optional[str] = Field(default=None, description="Scheduled arrival time e.g. '12:00'")
    duration_hours: float = Field(..., ge=0, description="Travel duration in hours")
    estimated_cost_inr: float = Field(..., ge=0, description="Estimated segment fare in INR")
    distance_km: Optional[float] = Field(default=None, ge=0, description="Segment distance in km")
    booking_url: Optional[str] = Field(default=None, description="Verified official booking or search handoff URL")
    availability_status: str = Field(default="Planning Estimate", description="Availability descriptor")
    transfer_duration_hours: Optional[float] = Field(default=None, ge=0, description="Transfer buffer time before next segment")
    connection_warning: Optional[str] = Field(default=None, description="Critical layover or transfer cautionary note")
    is_selected: bool = Field(default=False, description="User selection flag")


class ConnectedJourney(BaseModel):
    """Complete connected journey combining multiple transit legs from door to destination."""
    journey_id: str = Field(..., description="Unique journey itinerary identifier")
    route_type: str = Field(..., description="Route archetype e.g. 'Flight via Vijayawada Hub', 'Direct Train'")
    origin: str = Field(..., description="User starting location")
    origin_hub: Optional[str] = Field(default=None, description="Nearest departure airport or rail hub")
    destination_hub: Optional[str] = Field(default=None, description="Arrival airport or rail junction")
    final_destination: str = Field(..., description="End destination")
    segments: List[JourneySegment] = Field(default_factory=list, description="Ordered transit segments")
    total_duration_hours: float = Field(..., ge=0, description="Cumulative door-to-door duration in hours")
    total_transit_cost_inr: float = Field(..., ge=0, description="Sum of transit fares in INR")
    convenience_rating: str = Field(default="Balanced", description="'Fastest', 'Best Value', 'Scenic & Relaxed'")
    is_recommended: bool = Field(default=False, description="Flagged by planner as optimal path")
    is_selected: bool = Field(default=False, description="User selection flag")


class TravellerProfile(BaseModel):
    """Traveller contact details used for authorized booking prefill."""
    primary_contact_name: str = Field(default="Guest Traveller", description="Full name of primary traveller")
    email: str = Field(default="traveller@spirit-iq.internal", description="Contact email address")
    phone: str = Field(default="+91 9876543210", description="Contact telephone number")
    num_adults: int = Field(default=1, ge=1, description="Adult travellers count")
    num_children: int = Field(default=0, ge=0, description="Children count")
    special_notes: Optional[str] = Field(default=None, description="Dietary or accessibility notes")


class BookingOrder(BaseModel):
    """Booking transaction record with explicit payment approval gate."""
    order_id: str = Field(..., description="Unique booking order identifier e.g. 'ORD-7891'")
    trip_title: str = Field(..., description="Trip title associated with this order")
    status: BookingStatus = Field(default=BookingStatus.DRAFT, description="Current booking workflow state")
    traveller_profile: Optional[TravellerProfile] = Field(default=None, description="Customer contact info")
    selected_segments: List[JourneySegment] = Field(default_factory=list, description="Chosen transport legs")
    selected_hotel: Optional[HotelOption] = Field(default=None, description="Chosen accommodation")
    itemised_transport_inr: float = Field(default=0.0, ge=0, description="Transport total")
    itemised_hotel_inr: float = Field(default=0.0, ge=0, description="Hotel stay total")
    estimated_activities_inr: float = Field(default=0.0, ge=0, description="Estimated sightseeing & activities")
    estimated_food_inr: float = Field(default=0.0, ge=0, description="Estimated meals & dining")
    taxes_and_fees_inr: float = Field(default=0.0, ge=0, description="Estimated GST and platform charges")
    total_payable_inr: float = Field(default=0.0, ge=0, description="Grand total payable")
    user_explicitly_approved: bool = Field(default=False, description="Explicit approval gate confirmation")
    approval_timestamp: Optional[datetime.datetime] = Field(default=None, description="Timestamp of user authorization")
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now, description="Order timestamp")
    provider_handoff_notes: List[str] = Field(default_factory=list, description="Per-provider payment requirements")


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
    connected_journeys: List[ConnectedJourney] = Field(
        default_factory=list,
        description="Connected multi-segment journey routes with hub transfers",
    )
    hotel_recommendations: List[HotelOption] = Field(
        default_factory=list,
        description="Curated hotel options matching preferences",
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
    active_booking_order: Optional[BookingOrder] = Field(
        default=None,
        description="Active booking and payment approval state",
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings or tool failure notices",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent execution metadata, run ID, and timestamps",
    )
