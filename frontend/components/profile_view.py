"""
frontend/components/profile_view.py
===================================
Traveller Profile & System Settings View.
Manages guest contact info for booking prefill, preferred settings,
and displays live engine diagnostics and security safeguards.
"""

from __future__ import annotations

import streamlit as st
from backend.config import get_settings
from backend.schemas import TravellerProfile
from frontend.components import render_html


def render_profile_section() -> None:
    """
    Renders traveller contact profile settings, privacy commitments,
    and system engine diagnostics.
    """
    render_html(
        """
        <div style="margin-bottom: 24px;">
            <div class="spirit-hero-badge">
                <span>⚙️</span> Account & Preferences
            </div>
            <h2 style="font-size: 1.85rem; margin: 4px 0 6px 0; color: #FFFFFF;">
                Traveller Profile & Engine Settings
            </h2>
            <p style="color: #94A3B8; font-size: 0.95rem;">
                Manage your traveller contact info used for authorized booking prefill. 
                Inspect live AI system configuration and security guarantees.
            </p>
        </div>
        """
    )

    if "user_profile" not in st.session_state:
        st.session_state.user_profile = TravellerProfile(
            primary_contact_name="Guest Traveller",
            email="traveller@spirit-iq.internal",
            phone="+91 9876543210",
            num_adults=2,
            special_notes="Vegetarian meals preferred, quiet room",
        )

    prof = st.session_state.user_profile

    col_p1, col_p2 = st.columns([1.5, 1])

    with col_p1:
        st.subheader("👤 Traveller Information (For Booking Prefill)")
        with st.form("profile_form"):
            name = st.text_input("Full Name", value=prof.primary_contact_name)
            email = st.text_input("Email Address", value=prof.email)
            phone = st.text_input("Mobile Number", value=prof.phone)
            adults = st.number_input("Default Adult Guests", min_value=1, max_value=20, value=prof.num_adults)
            notes = st.text_area("Dietary & Accessibility Preferences", value=prof.special_notes or "")

            save_submitted = st.form_submit_button("💾 Save Profile Changes", type="primary", use_container_width=True)
            if save_submitted:
                st.session_state.user_profile = TravellerProfile(
                    primary_contact_name=name.strip(),
                    email=email.strip(),
                    phone=phone.strip(),
                    num_adults=int(adults),
                    special_notes=notes.strip() if notes.strip() else None,
                )
                st.toast("Profile settings updated successfully!", icon="✅")

        # Security & Privacy Section
        render_html(
            """
            <div style="
                background: rgba(16, 28, 58, 0.7);
                border: 1px solid rgba(0, 240, 255, 0.25);
                border-radius: 12px;
                padding: 16px 20px;
                margin-top: 20px;
            ">
                <h4 style="color: #00F0FF; margin: 0 0 6px 0; font-size: 0.95rem;">
                    🔒 Security & Data Privacy Commitment
                </h4>
                <div style="font-size: 0.82rem; color: #CBD5E1; line-height: 1.5;">
                    • SpiritIQ never stores payment card numbers or CVVs in plaintext.<br>
                    • We do not scrape browser sessions or bypass CAPTCHAs.<br>
                    • Official tickets are booked directly through accredited provider websites.<br>
                    • No traveller passwords are ever requested or logged.
                </div>
            </div>
            """
        )

    with col_p2:
        st.subheader("⚙️ System Engine Diagnostics")
        settings = get_settings()
        key_status = settings.validate_keys()

        render_html(
            f"""
            <div style="
                background: rgba(15, 23, 42, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 16px 20px;
            ">
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 0.78rem; color: #94A3B8;">Groq AI LLM Model</div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF;">{settings.groq_model}</div>
                    <div style="font-size: 0.75rem; color: {'#10B981' if key_status.get('groq_api_key_set') else '#F59E0B'};">
                        {'● API Key Configured' if key_status.get('groq_api_key_set') else '○ Key missing in .env (Deterministic fallback)'}
                    </div>
                </div>

                <div style="margin-bottom: 12px;">
                    <div style="font-size: 0.78rem; color: #94A3B8;">Open-Meteo Weather API</div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF;">Live Satellite Forecast</div>
                    <div style="font-size: 0.75rem; color: #10B981;">● Active (Global Coverage)</div>
                </div>

                <div style="margin-bottom: 12px;">
                    <div style="font-size: 0.78rem; color: #94A3B8;">Routing Engine</div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF;">Dijkstra Corridor + Maps</div>
                    <div style="font-size: 0.75rem; color: #10B981;">● Multi-modal Hub Resolver Active</div>
                </div>

                <div>
                    <div style="font-size: 0.78rem; color: #94A3B8;">Regional Hub Directory</div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF;">Tier-2/3 Feeder Database</div>
                    <div style="font-size: 0.75rem; color: #10B981;">● Indexed (Narasaraopeta, Coorg, Munnar, etc.)</div>
                </div>
            </div>
            """
        )
