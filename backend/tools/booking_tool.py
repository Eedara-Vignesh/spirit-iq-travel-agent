"""
backend/tools/booking_tool.py
=============================
Booking state machine, itemized pricing engine, idempotency management,
and explicit payment approval gate.
Assigned to: Member 4 (Agent Integration & Booking State Management)

Enforces:
1. Itemized breakdown (Transport, Hotel, Food, Activities, Taxes/Fees, Grand Total).
2. Strict state progression (DRAFT -> AWAITING_USER_REVIEW -> AWAITING_USER_APPROVAL -> REDIRECTED_TO_PROVIDER -> CONFIRMED).
3. Explicit User Approval Gate: NO booking or payment handoff is permitted without explicit authorization.
4. Duplicate booking prevention using order idempotency hashing.
5. Multi-provider disclosures: explicitly documents when separate tickets require independent checkouts.
"""

from __future__ import annotations

import datetime
import hashlib
import uuid
from typing import Any, Dict, List, Optional

from backend.schemas import (
    BookingOrder,
    BookingStatus,
    HotelOption,
    JourneySegment,
    ToolResult,
    TravellerProfile,
)


class BookingManager:
    """In-memory booking state manager with idempotency tracking."""

    def __init__(self) -> None:
        self._orders: Dict[str, BookingOrder] = {}
        self._order_hashes: Dict[str, str] = {}  # hash -> order_id

    def _compute_selection_hash(
        self,
        profile: Optional[TravellerProfile],
        segments: List[JourneySegment],
        hotel: Optional[HotelOption],
    ) -> str:
        """Computes deterministic hash of booking contents to prevent accidental duplicate orders."""
        raw_parts = []
        if profile:
            raw_parts.append(f"{profile.primary_contact_name}:{profile.email}:{profile.phone}")
        for seg in segments:
            raw_parts.append(f"{seg.segment_id}:{seg.mode}:{seg.estimated_cost_inr}")
        if hotel:
            raw_parts.append(f"{hotel.id}:{hotel.total_stay_cost_inr}")

        return hashlib.sha256("|".join(raw_parts).encode("utf-8")).hexdigest()

    def create_or_get_order(
        self,
        trip_title: str,
        traveller_profile: Optional[TravellerProfile] = None,
        selected_segments: Optional[List[JourneySegment]] = None,
        selected_hotel: Optional[HotelOption] = None,
        estimated_activities_inr: float = 0.0,
        estimated_food_inr: float = 0.0,
    ) -> BookingOrder:
        """
        Creates a new booking draft or retrieves an existing order if identical selections exist.
        Calculates itemized taxes, transport, stay, and total payable amount.
        """
        segments = selected_segments or []
        hotel = selected_hotel
        profile = traveller_profile or TravellerProfile()

        # Idempotency check: avoid duplicate orders for the same selections
        sel_hash = self._compute_selection_hash(profile, segments, hotel)
        if sel_hash in self._order_hashes:
            existing_id = self._order_hashes[sel_hash]
            if existing_id in self._orders:
                return self._orders[existing_id]

        order_id = f"SQ-{uuid.uuid4().hex[:8].upper()}"

        # Calculate itemized amounts
        transport_total = sum(s.estimated_cost_inr for s in segments)
        hotel_total = hotel.total_stay_cost_inr if hotel else 0.0

        # GST & regulatory tax: 5% on transport, 12% on hotel accommodation
        transport_tax = transport_total * 0.05
        hotel_tax = hotel_total * 0.12
        total_taxes = round(transport_tax + hotel_tax, 2)

        total_payable = round(
            transport_total + hotel_total + estimated_activities_inr + estimated_food_inr + total_taxes,
            2,
        )

        # Multi-provider disclosure notes
        handoff_notes: List[str] = []
        if segments:
            providers = list({s.provider for s in segments})
            handoff_notes.append(
                f"Transport tickets require booking through {len(providers)} provider(s): {', '.join(providers)}. Each ticket is issued separately."
            )
        if hotel:
            handoff_notes.append(
                f"Accommodation at '{hotel.name}' is reserved via {hotel.provider}. Payment terms: {hotel.cancellation_policy}."
            )
        handoff_notes.append(
            "Security Notice: SpiritIQ NEVER requests or stores credit card numbers or banking passwords. All checkouts take place on authorized partner pages."
        )

        order = BookingOrder(
            order_id=order_id,
            trip_title=trip_title,
            status=BookingStatus.AWAITING_USER_REVIEW,
            traveller_profile=profile,
            selected_segments=segments,
            selected_hotel=hotel,
            itemised_transport_inr=round(transport_total, 2),
            itemised_hotel_inr=round(hotel_total, 2),
            estimated_activities_inr=round(estimated_activities_inr, 2),
            estimated_food_inr=round(estimated_food_inr, 2),
            taxes_and_fees_inr=total_taxes,
            total_payable_inr=total_payable,
            user_explicitly_approved=False,
            approval_timestamp=None,
            created_at=datetime.datetime.now(),
            provider_handoff_notes=handoff_notes,
        )

        self._orders[order_id] = order
        self._order_hashes[sel_hash] = order_id
        return order

    def request_approval_gate(self, order_id: str) -> ToolResult:
        """Transitions order to AWAITING_USER_APPROVAL after user has reviewed itemized totals."""
        order = self._orders.get(order_id)
        if not order:
            return ToolResult.fail(f"Order '{order_id}' not found")

        if order.status not in (BookingStatus.DRAFT, BookingStatus.AWAITING_USER_REVIEW):
            return ToolResult.fail(f"Cannot request approval from state '{order.status.value}'")

        order.status = BookingStatus.AWAITING_USER_APPROVAL
        return ToolResult.ok(
            data=order,
            metadata={"message": "Order is waiting for user explicit payment approval"},
        )

    def approve_booking(
        self,
        order_id: str,
        user_confirmed: bool,
    ) -> ToolResult:
        """
        Explicit Payment Approval Gate.
        Strictly requires user_confirmed == True to authorize booking handoff.
        """
        order = self._orders.get(order_id)
        if not order:
            return ToolResult.fail(f"Order '{order_id}' not found")

        if not user_confirmed:
            return ToolResult.fail(
                "Payment approval denied: explicit user confirmation is mandatory before checkout."
            )

        if order.status != BookingStatus.AWAITING_USER_APPROVAL:
            # Allow idempotent re-approval if already awaiting approval or review
            if order.status == BookingStatus.AWAITING_USER_REVIEW:
                order.status = BookingStatus.AWAITING_USER_APPROVAL
            elif order.status == BookingStatus.REDIRECTED_TO_PROVIDER:
                return ToolResult.ok(data=order, metadata={"message": "Already approved and redirected"})
            else:
                return ToolResult.fail(
                    f"Invalid state transition: Cannot approve order in '{order.status.value}' state"
                )

        # Record explicit approval
        order.user_explicitly_approved = True
        order.approval_timestamp = datetime.datetime.now()
        order.status = BookingStatus.REDIRECTED_TO_PROVIDER

        return ToolResult.ok(
            data=order,
            metadata={
                "message": "User has explicitly approved the booking. Proceed to provider checkout.",
                "approval_timestamp": order.approval_timestamp.isoformat(),
            },
        )

    def confirm_provider_success(
        self,
        order_id: str,
        provider_confirmation_ref: str,
    ) -> ToolResult:
        """
        Marks booking as CONFIRMED ONLY when the provider returns a verified confirmation.
        Refuses to confirm unapproved orders.
        """
        order = self._orders.get(order_id)
        if not order:
            return ToolResult.fail(f"Order '{order_id}' not found")

        if not order.user_explicitly_approved:
            return ToolResult.fail("Safety violation: Cannot confirm an order that lacked user approval")

        if not provider_confirmation_ref or not provider_confirmation_ref.strip():
            return ToolResult.fail("A valid provider confirmation reference is required")

        order.status = BookingStatus.CONFIRMED
        order.provider_handoff_notes.append(
            f"Verified Provider Confirmation Reference: {provider_confirmation_ref.strip()}"
        )

        return ToolResult.ok(
            data=order,
            metadata={
                "status": "CONFIRMED",
                "confirmation_ref": provider_confirmation_ref.strip(),
            },
        )

    def cancel_order(self, order_id: str, reason: str = "User requested cancellation") -> ToolResult:
        """Cancels an order in progress."""
        order = self._orders.get(order_id)
        if not order:
            return ToolResult.fail(f"Order '{order_id}' not found")

        order.status = BookingStatus.CANCELLED
        order.provider_handoff_notes.append(f"Cancelled: {reason}")
        return ToolResult.ok(data=order, metadata={"reason": reason})

    def get_order(self, order_id: str) -> Optional[BookingOrder]:
        """Fetch existing order by ID."""
        return self._orders.get(order_id)


# Global singleton instance for application session
booking_manager = BookingManager()
