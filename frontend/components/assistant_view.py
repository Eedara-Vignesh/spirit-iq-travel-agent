"""
frontend/components/assistant_view.py
=====================================
Interactive AI Travel Assistant View.
Grounded in the active trip plan, destination weather, connected transport legs,
and hotel accommodations. Answers user inquiries and offers quick action prompt pills.
Powered by Groq high-speed AI inference.
"""

from __future__ import annotations

from typing import List, Optional
import streamlit as st
from groq import Groq

from backend.config import get_settings, sanitize_text
from backend.schemas import TripPlan
from frontend.components import render_html


def render_assistant_section(plan: Optional[TripPlan] = None) -> None:
    """
    Renders the conversational AI Travel Assistant interface.
    """
    render_html(
        """
        <div style="margin-bottom: 24px;">
            <div class="spirit-hero-badge">
                <span>💬</span> Intelligent Co-Pilot
            </div>
            <h2 style="font-size: 1.85rem; margin: 4px 0 6px 0; color: #FFFFFF;">
                SpiritIQ Travel Assistant
            </h2>
            <p style="color: #94A3B8; font-size: 0.95rem;">
                Ask questions about your trip, get local tips, clarify layover transfer buffers, 
                or ask for packing and culinary recommendations grounded in your itinerary.
            </p>
        </div>
        """
    )

    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = [
            {
                "role": "assistant",
                "content": (
                    "👋 Hello! I am SpiritIQ, your autonomous travel planning co-pilot powered by Groq. "
                    "I have full context of your itinerary, feeder connections, weather forecasts, and hotel choices. "
                    "How can I assist your journey today?"
                ),
            }
        ]

    # Quick Suggestion Chips
    render_html("<div style='font-size: 0.82rem; font-weight: 600; color: #94A3B8; margin-bottom: 8px;'>Suggested Prompts:</div>")
    chip_cols = st.columns(4)

    prompts = [
        "🎒 What should I pack for this trip?",
        "⏱️ Explain my connection & feeder transfer",
        "🍲 Recommend authentic regional dishes",
        "💡 How can I optimize my trip budget?",
    ]

    selected_prompt = None
    for i, p in enumerate(prompts):
        with chip_cols[i]:
            if st.button(p, key=f"chip_prompt_{i}", use_container_width=True):
                selected_prompt = p

    # Display chat history
    for msg in st.session_state.assistant_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    user_input = st.chat_input("Ask SpiritIQ anything about your trip...")
    active_query = user_input or selected_prompt

    if active_query:
        # Add user message
        st.session_state.assistant_messages.append({"role": "user", "content": active_query})
        with st.chat_message("user"):
            st.markdown(active_query)

        # Generate grounded response
        settings = get_settings()
        reply_text = ""

        # Build plan context
        context_parts = []
        if plan:
            context_parts.append(f"Trip Title: {plan.trip_title}")
            if plan.destinations:
                context_parts.append(f"Destination: {plan.destinations[0].name}")
            if plan.weather_summary:
                context_parts.append(f"Weather: {plan.weather_summary.conditions}, packing: {', '.join(plan.weather_summary.packing_recommendations)}")
            if plan.connected_journeys:
                cj = plan.connected_journeys[0]
                legs = " -> ".join(f"{s.leg_title} ({s.provider})" for s in cj.segments)
                context_parts.append(f"Connected Journey: {legs}")
            if plan.hotel_recommendations:
                context_parts.append(f"Hotel: {plan.hotel_recommendations[0].name} ({plan.hotel_recommendations[0].category.value})")

        plan_context = "\n".join(context_parts) if context_parts else "No active plan generated yet."

        if settings.groq_api_key and settings.groq_api_key.strip():
            try:
                client = Groq(api_key=settings.groq_api_key)
                system_instruction = (
                    "You are SpiritIQ, a world-class autonomous travel assistant. "
                    "Answer concisely, warmly, and helpfully using this verified trip context:\n"
                    f"{plan_context}\n"
                    "Always refer to real facts, layover times, and avoid hallucinating nonexistent airline flights."
                )
                response = client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": active_query},
                    ],
                    max_tokens=600,
                    temperature=0.7,
                )
                reply_text = (
                    response.choices[0].message.content
                    if response and response.choices and response.choices[0].message.content
                    else "I am here to help, but received an empty response."
                )
            except Exception as e:
                safe_err = sanitize_text(str(e), secrets=[settings.groq_api_key])
                reply_text = f"Notice: Live AI response encountered a temporary delay ({safe_err}). Here is your plan summary:\n{plan_context}"
        else:
            # Deterministic fallback grounded in active plan
            if "pack" in active_query.lower():
                packing = plan.weather_summary.packing_recommendations if (plan and plan.weather_summary) else ["Comfortable footwear", "Light cotton clothes", "Power bank", "Sun protection"]
                reply_text = f"🎒 **Packing Advice for {plan.destinations[0].name if (plan and plan.destinations) else 'your trip'}**:\n" + "\n".join(f"- {p}" for p in packing)
            elif "connection" in active_query.lower() or "transfer" in active_query.lower():
                if plan and plan.connected_journeys:
                    legs_desc = "\n".join(f"- **Leg {s.leg_number}**: {s.leg_title} via {s.provider} ({s.duration_hours:.1f} hrs)" for s in plan.connected_journeys[0].segments)
                    reply_text = f"📍 **Your Connected Multimodal Transfers**:\n{legs_desc}\n\n⚠️ Always allocate at least 2 hours layover buffer for security checks at hub junctions."
                else:
                    reply_text = "No multimodal legs are configured yet. Please generate a trip plan first."
            elif "dish" in active_query.lower() or "food" in active_query.lower():
                reply_text = "🍲 **Culinary Highlights**: Be sure to explore traditional local breakfast stalls, regional spice blends, and authentic thalis. In coastal areas, freshly prepared seafood and coconut-infused curries are unmissable!"
            else:
                reply_text = f"✨ **Trip Summary**:\n{plan_context}\n\nFeel free to ask for specific activity timings, packing advice, or transfer tips!"

        st.session_state.assistant_messages.append({"role": "assistant", "content": reply_text})
        with st.chat_message("assistant"):
            st.markdown(reply_text)
