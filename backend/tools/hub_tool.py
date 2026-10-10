"""
backend/tools/hub_tool.py
=========================
Regional Hub Resolver and Connected Multi-Modal Journey Planner.
Assigned to: Member 3 & Agent Orchestrator

Resolves nearest transport hubs (airports, railway junctions) for non-metro towns
(e.g., Narasaraopeta, Coorg, Ooty, Wayanad, Munnar, Hampi, Rishikesh, Manali),
and generates connected multi-leg itineraries with transfer times, connection
advisories, realistic fares, and official provider booking handoffs.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple
from backend.schemas import (
    ConnectedJourney,
    JourneySegment,
    ToolResult,
    TransportMode,
)

# Regional Hub Mapping for Tier-2 / Tier-3 towns and rural centers across India
REGIONAL_HUB_DIRECTORY: Dict[str, Dict[str, Any]] = {
    "narasaraopeta": {
        "city_name": "Narasaraopeta",
        "state": "Andhra Pradesh",
        "nearest_railway_junctions": [
            {"station": "Guntur Junction (GNT)", "distance_km": 46.0, "road_hours": 1.1, "transfer_cost_inr": 800.0},
            {"station": "Vijayawada Junction (BZA)", "distance_km": 82.0, "road_hours": 1.8, "transfer_cost_inr": 1400.0},
        ],
        "nearest_commercial_airports": [
            {"airport": "Vijayawada International Airport (VGA)", "distance_km": 95.0, "road_hours": 2.1, "transfer_cost_inr": 1600.0},
            {"airport": "Hyderabad Rajiv Gandhi International (HYD)", "distance_km": 240.0, "road_hours": 4.5, "transfer_cost_inr": 3800.0},
        ],
    },
    "coorg": {
        "city_name": "Coorg (Madikeri)",
        "state": "Karnataka",
        "nearest_railway_junctions": [
            {"station": "Mysuru Junction (MYS)", "distance_km": 118.0, "road_hours": 2.5, "transfer_cost_inr": 2200.0},
            {"station": "Mangaluru Central (MAQ)", "distance_km": 136.0, "road_hours": 3.2, "transfer_cost_inr": 2500.0},
        ],
        "nearest_commercial_airports": [
            {"airport": "Kannur International Airport (CNN)", "distance_km": 90.0, "road_hours": 2.2, "transfer_cost_inr": 2000.0},
            {"airport": "Mangaluru Airport (IXE)", "distance_km": 145.0, "road_hours": 3.5, "transfer_cost_inr": 2700.0},
            {"airport": "Bengaluru Kempegowda International (BLR)", "distance_km": 285.0, "road_hours": 5.5, "transfer_cost_inr": 4500.0},
        ],
    },
    "ooty": {
        "city_name": "Ooty (Udhagamandalam)",
        "state": "Tamil Nadu",
        "nearest_railway_junctions": [
            {"station": "Mettupalayam (MTP) / Toy Train", "distance_km": 52.0, "road_hours": 1.8, "transfer_cost_inr": 1200.0},
            {"station": "Coimbatore Junction (CBE)", "distance_km": 88.0, "road_hours": 2.7, "transfer_cost_inr": 1900.0},
        ],
        "nearest_commercial_airports": [
            {"airport": "Coimbatore International Airport (CJB)", "distance_km": 96.0, "road_hours": 2.8, "transfer_cost_inr": 2100.0},
        ],
    },
    "wayanad": {
        "city_name": "Wayanad (Kalpetta)",
        "state": "Kerala",
        "nearest_railway_junctions": [
            {"station": "Kozhikode Railway Station (CLT)", "distance_km": 72.0, "road_hours": 2.2, "transfer_cost_inr": 1600.0},
        ],
        "nearest_commercial_airports": [
            {"airport": "Calicut International Airport (CCJ)", "distance_km": 85.0, "road_hours": 2.5, "transfer_cost_inr": 1800.0},
            {"airport": "Kannur International Airport (CNN)", "distance_km": 95.0, "road_hours": 2.6, "transfer_cost_inr": 2000.0},
        ],
    },
    "munnar": {
        "city_name": "Munnar",
        "state": "Kerala",
        "nearest_railway_junctions": [
            {"station": "Aluva Railway Station (AWY)", "distance_km": 108.0, "road_hours": 3.2, "transfer_cost_inr": 2400.0},
            {"station": "Ernakulam Junction (ERS)", "distance_km": 126.0, "road_hours": 3.8, "transfer_cost_inr": 2800.0},
        ],
        "nearest_commercial_airports": [
            {"airport": "Cochin International Airport (COK)", "distance_km": 110.0, "road_hours": 3.2, "transfer_cost_inr": 2500.0},
        ],
    },
    "manali": {
        "city_name": "Manali",
        "state": "Himachal Pradesh",
        "nearest_railway_junctions": [
            {"station": "Chandigarh Junction (CDG)", "distance_km": 285.0, "road_hours": 7.0, "transfer_cost_inr": 4800.0},
        ],
        "nearest_commercial_airports": [
            {"airport": "Kullu-Manali Airport, Bhuntar (KUU)", "distance_km": 50.0, "road_hours": 1.5, "transfer_cost_inr": 1500.0},
            {"airport": "Chandigarh International Airport (IXC)", "distance_km": 295.0, "road_hours": 7.5, "transfer_cost_inr": 5000.0},
        ],
    },
    "kerala": {
        "city_name": "Kerala (Kochi Hub)",
        "state": "Kerala",
        "nearest_railway_junctions": [
            {"station": "Ernakulam Junction (ERS)", "distance_km": 0.0, "road_hours": 0.5, "transfer_cost_inr": 300.0},
        ],
        "nearest_commercial_airports": [
            {"airport": "Cochin International Airport (COK)", "distance_km": 30.0, "road_hours": 0.9, "transfer_cost_inr": 900.0},
        ],
    },
    "goa": {
        "city_name": "Goa (Panaji)",
        "state": "Goa",
        "nearest_railway_junctions": [
            {"station": "Madgaon Junction (MAO)", "distance_km": 34.0, "road_hours": 0.8, "transfer_cost_inr": 800.0},
        ],
        "nearest_commercial_airports": [
            {"airport": "Dabolim Airport (GOI) / Mopa (GOX)", "distance_km": 28.0, "road_hours": 0.7, "transfer_cost_inr": 950.0},
        ],
    },
}


def resolve_transport_hubs(location: str) -> Optional[Dict[str, Any]]:
    """Resolve transport hub availability and nearest airports/railway junctions for a location."""
    clean = location.strip().lower()
    for key, data in REGIONAL_HUB_DIRECTORY.items():
        if key in clean or clean in key:
            return data
    return None


def generate_connected_journeys(
    origin: str,
    destination: str,
    num_travellers: int = 1,
    preferences: Optional[List[TransportMode]] = None,
) -> ToolResult:
    """
    Plan connected multi-leg journeys connecting origin to destination.
    Identifies feeder transfers to major hubs when origin lacks direct commercial links.
    """
    if not origin or not origin.strip() or not destination or not destination.strip():
        return ToolResult.fail("Origin and destination must be provided for connected journey planning")

    origin_clean = origin.strip().title()
    dest_clean = destination.strip().title()
    prefs = preferences or [TransportMode.ANY]

    origin_hub_data = resolve_transport_hubs(origin)
    dest_hub_data = resolve_transport_hubs(destination)

    # 1. Determine Departure Hubs
    dep_airport_hub = "Nearest Regional Airport"
    dep_airport_road_km = 30.0
    dep_airport_road_hours = 0.8
    dep_airport_road_cost = 600.0

    dep_rail_hub = f"{origin_clean} Railway Station"
    dep_rail_road_km = 10.0
    dep_rail_road_hours = 0.4
    dep_rail_road_cost = 250.0

    if origin_hub_data:
        if origin_hub_data.get("nearest_commercial_airports"):
            best_air = origin_hub_data["nearest_commercial_airports"][0]
            dep_airport_hub = best_air["airport"]
            dep_airport_road_km = best_air["distance_km"]
            dep_airport_road_hours = best_air["road_hours"]
            dep_airport_road_cost = best_air["transfer_cost_inr"]

        if origin_hub_data.get("nearest_railway_junctions"):
            best_rail = origin_hub_data["nearest_railway_junctions"][0]
            dep_rail_hub = best_rail["station"]
            dep_rail_road_km = best_rail["distance_km"]
            dep_rail_road_hours = best_rail["road_hours"]
            dep_rail_road_cost = best_rail["transfer_cost_inr"]

    # 2. Determine Arrival Hubs
    arr_airport_hub = f"{dest_clean} Airport"
    arr_rail_hub = f"{dest_clean} Railway Station"
    arr_local_road_hours = 0.8
    arr_local_road_cost = 500.0

    if dest_hub_data:
        if dest_hub_data.get("nearest_commercial_airports"):
            best_dest_air = dest_hub_data["nearest_commercial_airports"][0]
            arr_airport_hub = best_dest_air["airport"]
        if dest_hub_data.get("nearest_railway_junctions"):
            best_dest_rail = dest_hub_data["nearest_railway_junctions"][0]
            arr_rail_hub = best_dest_rail["station"]

    journeys: List[ConnectedJourney] = []

    # -------------------------------------------------------------
    # Option 1: Connected Flight Journey (Road Feeder + Flight + Hotel Drop)
    # -------------------------------------------------------------
    if TransportMode.ANY in prefs or TransportMode.FLIGHT in prefs:
        flight_leg_cost = 4500.0 * num_travellers
        flight_duration = 3.5  # Includes connection / air time
        tot_air_time = round(dep_airport_road_hours + 2.0 + flight_duration + arr_local_road_hours, 1)
        tot_air_cost = round(dep_airport_road_cost + flight_leg_cost + arr_local_road_cost, 0)

        seg1 = JourneySegment(
            segment_id=f"seg-{uuid.uuid4().hex[:6]}",
            leg_number=1,
            leg_title=f"Feeder Road Transfer: {origin_clean} -> {dep_airport_hub.split('(')[0].strip()}",
            origin=origin_clean,
            destination=dep_airport_hub,
            mode=TransportMode.CAB,
            provider="Prepaid Outstation Cab / Taxi Transfer",
            departure_time="05:30",
            arrival_time="07:45",
            duration_hours=dep_airport_road_hours,
            estimated_cost_inr=dep_airport_road_cost,
            distance_km=dep_airport_road_km,
            booking_url="https://www.makemytrip.com/cabs/",
            availability_status="Frequent Highway Corridor",
            transfer_duration_hours=2.0,
            connection_warning=f"Crucial Airport Buffer: Arrive at {dep_airport_hub.split('(')[0].strip()} at least 2 hours before flight departure.",
            is_selected=True,
        )

        seg2 = JourneySegment(
            segment_id=f"seg-{uuid.uuid4().hex[:6]}",
            leg_number=2,
            leg_title=f"Domestic Air Link: {dep_airport_hub.split('(')[0].strip()} -> {arr_airport_hub.split('(')[0].strip()}",
            origin=dep_airport_hub,
            destination=arr_airport_hub,
            mode=TransportMode.FLIGHT,
            provider="IndiGo / Air India Domestic (Benchmark Fares)",
            departure_time="09:45",
            arrival_time="13:15",
            duration_hours=flight_duration,
            estimated_cost_inr=flight_leg_cost,
            distance_km=620.0,
            booking_url="https://www.makemytrip.com/flights/",
            availability_status="Partner Fares & Real-time Booking",
            transfer_duration_hours=0.5,
            connection_warning="Baggage collection and terminal exit: ~30-45 minutes.",
            is_selected=True,
        )

        seg3 = JourneySegment(
            segment_id=f"seg-{uuid.uuid4().hex[:6]}",
            leg_number=3,
            leg_title=f"Destination Hotel Transfer: {arr_airport_hub.split('(')[0].strip()} -> Stay Venue in {dest_clean}",
            origin=arr_airport_hub,
            destination=f"{dest_clean} Hotel / Resort",
            mode=TransportMode.CAB,
            provider="Airport Prepaid Taxi / Ola Outstation",
            departure_time="14:00",
            arrival_time="14:50",
            duration_hours=arr_local_road_hours,
            estimated_cost_inr=arr_local_road_cost,
            distance_km=32.0,
            booking_url="https://www.makemytrip.com/cabs/",
            availability_status="24/7 Airport Taxi Booths",
            transfer_duration_hours=0.0,
            connection_warning=None,
            is_selected=True,
        )

        journeys.append(
            ConnectedJourney(
                journey_id=f"journey-air-{uuid.uuid4().hex[:6]}",
                route_type=f"Fastest Air Link (via {dep_airport_hub.split('(')[0].strip()})",
                origin=origin_clean,
                origin_hub=dep_airport_hub,
                destination_hub=arr_airport_hub,
                final_destination=dest_clean,
                segments=[seg1, seg2, seg3],
                total_duration_hours=tot_air_time,
                total_transit_cost_inr=tot_air_cost,
                convenience_rating="Fastest",
                is_recommended=True,
                is_selected=True,
            )
        )

    # -------------------------------------------------------------
    # Option 2: Connected Rail Journey (Feeder + Superfast Train + Local Drop)
    # -------------------------------------------------------------
    if TransportMode.ANY in prefs or TransportMode.TRAIN in prefs:
        train_fare = 1550.0 * num_travellers
        train_duration = 16.5  # Typical overnight or superfast intercity run
        tot_rail_time = round(dep_rail_road_hours + 1.0 + train_duration + 0.6, 1)
        tot_rail_cost = round(dep_rail_road_cost + train_fare + 350.0, 0)

        r_seg1 = JourneySegment(
            segment_id=f"seg-{uuid.uuid4().hex[:6]}",
            leg_number=1,
            leg_title=f"Station Transfer: {origin_clean} -> {dep_rail_hub.split('(')[0].strip()}",
            origin=origin_clean,
            destination=dep_rail_hub,
            mode=TransportMode.CAB,
            provider="Local Taxi / Station Feeder Bus",
            departure_time="14:30",
            arrival_time="15:45",
            duration_hours=dep_rail_road_hours,
            estimated_cost_inr=dep_rail_road_cost,
            distance_km=dep_rail_road_km,
            booking_url="https://www.redbus.in/",
            availability_status="Frequent Daily Transfers",
            transfer_duration_hours=1.0,
            connection_warning=f"Platform Buffer: Reach {dep_rail_hub.split('(')[0].strip()} at least 45 minutes before departure.",
            is_selected=False,
        )

        r_seg2 = JourneySegment(
            segment_id=f"seg-{uuid.uuid4().hex[:6]}",
            leg_number=2,
            leg_title=f"Superfast / Express Train: {dep_rail_hub.split('(')[0].strip()} -> {arr_rail_hub.split('(')[0].strip()}",
            origin=dep_rail_hub,
            destination=arr_rail_hub,
            mode=TransportMode.TRAIN,
            provider="Indian Railways (IRCTC Superfast / Express 3AC)",
            departure_time="16:45",
            arrival_time="09:15",
            duration_hours=train_duration,
            estimated_cost_inr=train_fare,
            distance_km=840.0,
            booking_url="https://www.irctc.co.in/",
            availability_status="Official IRCTC Ticket Booking",
            transfer_duration_hours=0.3,
            connection_warning="Confirm PNR status 4 hours prior to chart preparation.",
            is_selected=False,
        )

        r_seg3 = JourneySegment(
            segment_id=f"seg-{uuid.uuid4().hex[:6]}",
            leg_number=3,
            leg_title=f"Station Auto/Cab Drop: {arr_rail_hub.split('(')[0].strip()} -> Hotel in {dest_clean}",
            origin=arr_rail_hub,
            destination=f"{dest_clean} Hotel / Stay",
            mode=TransportMode.CAB,
            provider="Station Prepaid Auto / Cab Booth",
            departure_time="09:35",
            arrival_time="10:10",
            duration_hours=0.6,
            estimated_cost_inr=350.0,
            distance_km=15.0,
            booking_url="https://www.makemytrip.com/cabs/",
            availability_status="Station Stand Available",
            transfer_duration_hours=0.0,
            connection_warning=None,
            is_selected=False,
        )

        journeys.append(
            ConnectedJourney(
                journey_id=f"journey-rail-{uuid.uuid4().hex[:6]}",
                route_type=f"Best Value Train (via {dep_rail_hub.split('(')[0].strip()})",
                origin=origin_clean,
                origin_hub=dep_rail_hub,
                destination_hub=arr_rail_hub,
                final_destination=dest_clean,
                segments=[r_seg1, r_seg2, r_seg3],
                total_duration_hours=tot_rail_time,
                total_transit_cost_inr=tot_rail_cost,
                convenience_rating="Best Value",
                is_recommended=(TransportMode.TRAIN in prefs),
                is_selected=False,
            )
        )

    # -------------------------------------------------------------
    # Option 3: Highway Express Sleeper Bus Corridor
    # -------------------------------------------------------------
    if TransportMode.ANY in prefs or TransportMode.BUS in prefs:
        bus_fare = 1750.0 * num_travellers
        bus_duration = 18.0
        tot_bus_time = round(1.0 + bus_duration + 0.5, 1)
        tot_bus_cost = round(300.0 + bus_fare + 300.0, 0)

        b_seg1 = JourneySegment(
            segment_id=f"seg-{uuid.uuid4().hex[:6]}",
            leg_number=1,
            leg_title=f"Boarding Point Transfer: {origin_clean} -> Intercity Bus Terminal",
            origin=origin_clean,
            destination=f"{dep_rail_hub.split('(')[0].strip()} Bus Stand",
            mode=TransportMode.CAB,
            provider="Local Auto / City Cab",
            departure_time="17:00",
            arrival_time="18:00",
            duration_hours=1.0,
            estimated_cost_inr=300.0,
            distance_km=35.0,
            booking_url="https://www.redbus.in/",
            availability_status="Daily Urban Transit",
            transfer_duration_hours=0.5,
            connection_warning="Boarding Gate: Arrive 30 minutes before bus departure.",
            is_selected=False,
        )

        b_seg2 = JourneySegment(
            segment_id=f"seg-{uuid.uuid4().hex[:6]}",
            leg_number=2,
            leg_title=f"Multi-Axle AC Sleeper Bus: Regional Terminal -> {dest_clean} Central",
            origin=f"{dep_rail_hub.split('(')[0].strip()} Bus Stand",
            destination=f"{dest_clean} Central Stand",
            mode=TransportMode.BUS,
            provider="Intercity AC Multi-Axle Volvo (KSRTC / Private Sleeper)",
            departure_time="18:30",
            arrival_time="12:30",
            duration_hours=bus_duration,
            estimated_cost_inr=bus_fare,
            distance_km=750.0,
            booking_url="https://www.redbus.in/",
            availability_status="RedBus Verified Partner Tickets",
            transfer_duration_hours=0.2,
            connection_warning="Night highway journey: Dinner stop at highway plaza.",
            is_selected=False,
        )

        b_seg3 = JourneySegment(
            segment_id=f"seg-{uuid.uuid4().hex[:6]}",
            leg_number=3,
            leg_title=f"Last-Mile Cab Drop: {dest_clean} Central -> Hotel",
            origin=f"{dest_clean} Central Stand",
            destination=f"{dest_clean} Hotel Venue",
            mode=TransportMode.CAB,
            provider="City Cab / Auto",
            departure_time="12:45",
            arrival_time="13:15",
            duration_hours=0.5,
            estimated_cost_inr=300.0,
            distance_km=10.0,
            booking_url="https://www.makemytrip.com/cabs/",
            availability_status="Local Stand",
            transfer_duration_hours=0.0,
            connection_warning=None,
            is_selected=False,
        )

        journeys.append(
            ConnectedJourney(
                journey_id=f"journey-bus-{uuid.uuid4().hex[:6]}",
                route_type=f"Overnight Highway Bus (via Regional Arterial)",
                origin=origin_clean,
                origin_hub=dep_rail_hub,
                destination_hub=f"{dest_clean} Central",
                final_destination=dest_clean,
                segments=[b_seg1, b_seg2, b_seg3],
                total_duration_hours=tot_bus_time,
                total_transit_cost_inr=tot_bus_cost,
                convenience_rating="Budget Friendly",
                is_recommended=(TransportMode.BUS in prefs and TransportMode.FLIGHT not in prefs),
                is_selected=False,
            )
        )

    return ToolResult.ok(
        data=journeys,
        metadata={
            "tool": "hub_tool",
            "origin": origin_clean,
            "destination": dest_clean,
            "origin_hub_resolved": bool(origin_hub_data),
            "journey_options_count": len(journeys),
        },
    )
