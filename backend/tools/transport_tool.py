"""
backend/tools/transport_tool.py
===============================
Transportation comparison tool.
Assigned to: Member 3 (Routing, Dijkstra, Transport and Budget)

Compares transit modes (flight, train, bus, cab, self_drive) with realistic
benchmarked durations, costs per passenger, and clear estimation disclaimers.
"""

from __future__ import annotations

from typing import List, Optional
from backend.schemas import ToolResult, TransportMode, TransportOption


def compare_transport_options(
    origin: str,
    destination: str,
    distance_km: Optional[float] = None,
    preferences: Optional[List[TransportMode]] = None,
    num_travellers: int = 1,
) -> ToolResult:
    """
    Compare transit modes between origin and destination.
    Clearly notes that all timings and fares are calibrated benchmarks,
    not live provider booking inventory.
    """
    prefs = preferences or [TransportMode.ANY]
    dist = distance_km or 350.0  # default typical intercity distance

    options: List[TransportOption] = []

    # 1. Flight (Sensible for distances >= 300 km or where airports exist)
    if dist >= 250.0 and (TransportMode.ANY in prefs or TransportMode.FLIGHT in prefs):
        flight_cost = round(3200.0 + (dist * 2.5), -2)  # Benchmark ~₹3500-6000
        flight_dur = round(1.0 + (dist / 600.0), 1)
        options.append(
            TransportOption(
                mode=TransportMode.FLIGHT,
                provider_or_route="Domestic Airline (IndiGo / Air India benchmark)",
                departure_point=f"{origin} Airport",
                arrival_point=f"{destination} / Nearest Hub",
                duration_hours=flight_dur,
                estimated_cost_inr=flight_cost,
                booking_url="https://www.makemytrip.com/flights/",
                is_recommended=(dist > 600.0),
            )
        )

    # 2. Train (Super-fast / Express / Vande Bharat benchmarks)
    if TransportMode.ANY in prefs or TransportMode.TRAIN in prefs:
        train_cost = round(600.0 + (dist * 1.5), -1)  # Benchmark 3AC / CC fare
        train_dur = round(max(2.0, dist / 65.0), 1)
        options.append(
            TransportOption(
                mode=TransportMode.TRAIN,
                provider_or_route="Indian Railways (Vande Bharat / Express 3AC)",
                departure_point=f"{origin} Railway Station",
                arrival_point=f"{destination} / Nearest Junction",
                duration_hours=train_dur,
                estimated_cost_inr=train_cost,
                booking_url="https://www.irctc.co.in/",
                is_recommended=(200.0 <= dist <= 600.0),
            )
        )

    # 3. Intercity Bus (AC Sleeper / Multi-Axle)
    if TransportMode.ANY in prefs or TransportMode.BUS in prefs:
        bus_cost = round(500.0 + (dist * 1.6), -1)
        bus_dur = round(max(3.0, dist / 48.0), 1)
        options.append(
            TransportOption(
                mode=TransportMode.BUS,
                provider_or_route="Intercity AC Sleeper (KSRTC / Private Volvo)",
                departure_point=f"{origin} Central Bus Stand",
                arrival_point=f"{destination} Bus Stand",
                duration_hours=bus_dur,
                estimated_cost_inr=bus_cost,
                booking_url="https://www.redbus.in/",
                is_recommended=(dist < 350.0),
            )
        )

    # 4. Outstation Cab / Self-Drive
    if TransportMode.ANY in prefs or TransportMode.CAB in prefs or TransportMode.SELF_DRIVE in prefs:
        # Cab cost is total for vehicle (~₹14/km + toll allowance)
        total_cab_cost = round((dist * 14.0) + 500.0, -2)
        cab_cost_per_person = round(total_cab_cost / max(1, num_travellers), 0)
        cab_dur = round(max(2.0, dist / 55.0), 1)
        options.append(
            TransportOption(
                mode=TransportMode.CAB,
                provider_or_route="Outstation Sedan/SUV (MakeMyTrip / Ola Outstation)",
                departure_point=f"{origin} Doorstep Pickup",
                arrival_point=f"{destination} Hotel Drop",
                duration_hours=cab_dur,
                estimated_cost_inr=cab_cost_per_person,
                booking_url="https://www.makemytrip.com/cabs/",
                is_recommended=(dist < 300.0 and num_travellers >= 3),
            )
        )

    return ToolResult.ok(
        data={"transport_options": [o.model_dump() for o in options]},
        metadata={
            "tool": "transport_tool",
            "distance_km": dist,
            "disclaimer": "Fares and travel durations are calibrated benchmark estimates based on Indian transit standards. Real-time availability requires live operator queries.",
        },
    )
