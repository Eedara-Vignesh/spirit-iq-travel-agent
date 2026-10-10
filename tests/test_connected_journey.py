"""
tests/test_connected_journey.py
================================
Unit and regression tests for Connected Multi-Modal Journey Planning & Hub Resolution.
Verifies hub routing for non-metro towns (e.g. Narasaraopeta, Coorg, Ooty, Munnar),
segment division, layover warnings, and verified booking handoffs.
"""

import pytest
from backend.schemas import TransportMode
from backend.tools.hub_tool import generate_connected_journeys, resolve_transport_hubs


def test_hub_resolution_narasaraopeta():
    """Verify Narasaraopeta correctly resolves to Vijayawada & Guntur hubs without pretending to have an airport."""
    hubs = resolve_transport_hubs("Narasaraopeta")
    assert hubs is not None
    assert hubs["city_name"] == "Narasaraopeta"

    # Commercial airports
    airports = hubs["nearest_commercial_airports"]
    assert len(airports) >= 1
    assert "Vijayawada" in airports[0]["airport"]
    assert airports[0]["distance_km"] > 0
    assert airports[0]["transfer_cost_inr"] > 0

    # Railway junctions
    rails = hubs["nearest_railway_junctions"]
    assert len(rails) >= 1
    station_names = [r["station"] for r in rails]
    assert any("Vijayawada" in s or "Guntur" in s for s in station_names)


def test_hub_resolution_coorg_and_munnar():
    """Verify hill stations without airports resolve to regional hubs."""
    coorg_hubs = resolve_transport_hubs("Coorg")
    assert coorg_hubs is not None
    airports = [a["airport"] for a in coorg_hubs["nearest_commercial_airports"]]
    assert any("Kannur" in a or "Mangaluru" in a or "Mysuru" in a for a in airports)

    munnar_hubs = resolve_transport_hubs("Munnar")
    assert munnar_hubs is not None
    assert any("Cochin" in a["airport"] for a in munnar_hubs["nearest_commercial_airports"])


def test_generate_connected_journeys_narasaraopeta_to_kerala():
    """
    Test end-to-end connected journey generation for Narasaraopeta -> Kerala.
    Must generate 3 distinct routes (Air Link, Rail Corridor, Highway Sleeper).
    """
    res = generate_connected_journeys(
        origin="Narasaraopeta",
        destination="Kerala",
        num_travellers=2,
        preferences=[TransportMode.FLIGHT, TransportMode.TRAIN, TransportMode.BUS],
    )
    assert res.success is True
    journeys = res.data
    assert len(journeys) >= 3

    # Check Route 1: Air Link via Vijayawada Hub
    air_route = next((j for j in journeys if "Flight" in j.route_type or "Air" in j.route_type), None)
    assert air_route is not None
    assert len(air_route.segments) == 3

    # Leg 1: Feeder road transfer
    leg1 = air_route.segments[0]
    assert leg1.leg_number == 1
    assert "Narasaraopeta" in leg1.origin
    assert "Vijayawada" in leg1.destination
    assert leg1.mode in (TransportMode.CAB, TransportMode.BUS)

    # Leg 2: Inter-hub flight
    leg2 = air_route.segments[1]
    assert leg2.leg_number == 2
    assert leg2.mode == TransportMode.FLIGHT
    assert leg2.transfer_duration_hours is not None

    # Leg 3: Local transfer to final destination
    leg3 = air_route.segments[2]
    assert leg3.leg_number == 3
    assert "Kerala" in leg3.destination or "Kochi" in leg3.destination

    # Totals check
    assert air_route.total_duration_hours > 0
    assert air_route.total_transit_cost_inr > 0
    assert any(s.connection_warning is not None for s in air_route.segments)


def test_generate_connected_journeys_empty_locations():
    """Verify validation fails when origin or destination is empty."""
    res = generate_connected_journeys(origin="", destination="Goa")
    assert res.success is False
    assert "must be provided" in res.error.lower()

    res2 = generate_connected_journeys(origin="Delhi", destination="")
    assert res2.success is False
