"""
tests/test_booking_workflow.py
==============================
Unit tests for Booking State Machine & Explicit Payment Approval Gate.
Verifies itemized pricing, duplicate order idempotency, strict state transitions,
mandatory user approval, and confirmation verification.
"""

import pytest
from backend.schemas import (
    BookingStatus,
    HotelCategory,
    HotelOption,
    JourneySegment,
    TransportMode,
    TravellerProfile,
)
from backend.tools.booking_tool import BookingManager


@pytest.fixture
def manager():
    return BookingManager()


@pytest.fixture
def sample_segment():
    return JourneySegment(
        segment_id="SEG-01",
        leg_number=1,
        leg_title="Test Flight Leg",
        origin="Vijayawada",
        destination="Kochi",
        mode=TransportMode.FLIGHT,
        provider="IndiGo",
        duration_hours=2.5,
        estimated_cost_inr=5500.0,
    )


@pytest.fixture
def sample_hotel():
    return HotelOption(
        id="HTL-01",
        name="Kerala Lagoon Retreat",
        location="Kochi",
        destination="Kerala",
        category=HotelCategory.RESORT,
        rating=4.7,
        price_per_night_inr=6000.0,
        total_stay_cost_inr=18000.0,
        booking_url="https://booking.com/example",
    )


def test_booking_order_creation_and_pricing(manager, sample_segment, sample_hotel):
    """Verify itemized pricing calculation with transport, hotel, GST taxes, and totals."""
    profile = TravellerProfile(primary_contact_name="Alice Smith", email="alice@test.com")
    order = manager.create_or_get_order(
        trip_title="Kochi Holiday",
        traveller_profile=profile,
        selected_segments=[sample_segment],
        selected_hotel=sample_hotel,
        estimated_activities_inr=2000.0,
        estimated_food_inr=3000.0,
    )

    assert order.order_id.startswith("SQ-")
    assert order.status == BookingStatus.AWAITING_USER_REVIEW
    assert order.itemised_transport_inr == 5500.0
    assert order.itemised_hotel_inr == 18000.0
    assert order.estimated_activities_inr == 2000.0
    assert order.estimated_food_inr == 3000.0

    # 5% on 5500 (275) + 12% on 18000 (2160) = 2435
    assert abs(order.taxes_and_fees_inr - 2435.0) < 0.01
    # Total = 5500 + 18000 + 2000 + 3000 + 2435 = 30935
    assert abs(order.total_payable_inr - 30935.0) < 0.01
    assert order.user_explicitly_approved is False


def test_booking_order_idempotency(manager, sample_segment, sample_hotel):
    """Verify identical booking selections return the same order without creating duplicates."""
    profile = TravellerProfile(primary_contact_name="Bob", email="bob@test.com", phone="+91 9999999999")
    order1 = manager.create_or_get_order(
        trip_title="Trip 1",
        traveller_profile=profile,
        selected_segments=[sample_segment],
        selected_hotel=sample_hotel,
    )
    order2 = manager.create_or_get_order(
        trip_title="Trip 1",
        traveller_profile=profile,
        selected_segments=[sample_segment],
        selected_hotel=sample_hotel,
    )
    assert order1.order_id == order2.order_id


def test_payment_approval_gate_enforcement(manager, sample_segment, sample_hotel):
    """Verify approval strictly requires user confirmation flag."""
    order = manager.create_or_get_order(
        trip_title="Approval Test",
        selected_segments=[sample_segment],
        selected_hotel=sample_hotel,
    )

    # 1. Advance to AWAITING_USER_APPROVAL
    rev_res = manager.request_approval_gate(order.order_id)
    assert rev_res.success is True
    assert order.status == BookingStatus.AWAITING_USER_APPROVAL

    # 2. Denied approval
    reject_res = manager.approve_booking(order.order_id, user_confirmed=False)
    assert reject_res.success is False
    assert "mandatory" in reject_res.error.lower()
    assert order.user_explicitly_approved is False

    # 3. Explicit approval
    approve_res = manager.approve_booking(order.order_id, user_confirmed=True)
    assert approve_res.success is True
    assert order.user_explicitly_approved is True
    assert order.approval_timestamp is not None
    assert order.status == BookingStatus.REDIRECTED_TO_PROVIDER


def test_provider_confirmation_validation(manager, sample_segment):
    """Verify order cannot be confirmed without explicit approval and valid reference."""
    order = manager.create_or_get_order(
        trip_title="Confirmation Test",
        selected_segments=[sample_segment],
    )

    # Attempt to confirm without approval must fail
    fail_res = manager.confirm_provider_success(order.order_id, "REF-12345")
    assert fail_res.success is False
    assert "safety violation" in fail_res.error.lower()

    # Now approve
    manager.request_approval_gate(order.order_id)
    manager.approve_booking(order.order_id, user_confirmed=True)

    # Missing ref must fail
    empty_ref_res = manager.confirm_provider_success(order.order_id, "")
    assert empty_ref_res.success is False

    # Valid confirmation
    confirm_res = manager.confirm_provider_success(order.order_id, "IRCTC-PNR-9876543210")
    assert confirm_res.success is True
    assert order.status == BookingStatus.CONFIRMED
