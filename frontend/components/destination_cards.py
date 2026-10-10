"""
frontend/components/destination_cards.py
========================================
Interactive destination discovery cards with reliable imagery,
seasonality tags, highlights, and instant form selection.
"""

from __future__ import annotations
from typing import Callable, Optional
import streamlit as st
from frontend.components import render_html

# Curated reference destinations with reliable imagery & fallback gradients
FEATURED_DESTINATIONS = [
    {
        "name": "Goa",
        "state": "Goa, India",
        "tagline": "Golden shores, Portuguese heritage, and vibrant coastal cuisine.",
        "image": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=700&q=80",
        "fallback_gradient": "linear-gradient(135deg, #0077b6, #00b4d8)",
        "icon": "🏖️",
        "season": "Oct – Mar (Pleasant Coastal)",
        "budget_from": "₹25,000",
        "tags": ["Beaches", "Heritage", "Nightlife", "Water Sports"],
    },
    {
        "name": "Coorg (Kodagu)",
        "state": "Karnataka, India",
        "tagline": "The Scotland of India — misty emerald hills and coffee estates.",
        "image": "https://images.unsplash.com/photo-1596401057633-54a8fe8ef647?auto=format&fit=crop&w=700&q=80",
        "fallback_gradient": "linear-gradient(135deg, #1b4332, #2d6a4f)",
        "icon": "☕",
        "season": "Oct – Apr (Misty & Crisp)",
        "budget_from": "₹18,000",
        "tags": ["Coffee Plantations", "Waterfalls", "Trekking", "Scenic"],
    },
    {
        "name": "Udaipur",
        "state": "Rajasthan, India",
        "tagline": "The City of Lakes — royal palaces, heritage havelis, and boat rides.",
        "image": "https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=700&q=80",
        "fallback_gradient": "linear-gradient(135deg, #b5179e, #7209b7)",
        "icon": "🏰",
        "season": "Oct – Mar (Desert Winter)",
        "budget_from": "₹28,000",
        "tags": ["Palaces", "Lakes", "Royal Heritage", "Culture"],
    },
    {
        "name": "Ooty",
        "state": "Tamil Nadu, India",
        "tagline": "Queen of the Nilgiris — rolling tea hills and historic toy train.",
        "image": "https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?auto=format&fit=crop&w=700&q=80",
        "fallback_gradient": "linear-gradient(135deg, #2b9348, #55a630)",
        "icon": "🚂",
        "season": "Oct – May (Refreshing Cool)",
        "budget_from": "₹20,000",
        "tags": ["Toy Train", "Tea Gardens", "Pine Forests", "Cool Clime"],
    },
    {
        "name": "Jaipur",
        "state": "Rajasthan, India",
        "tagline": "The Pink City — historic hilltop forts, vibrant bazaars, and palaces.",
        "image": "https://images.unsplash.com/photo-1603262110263-fb010d6e75dc?auto=format&fit=crop&w=700&q=80",
        "fallback_gradient": "linear-gradient(135deg, #c9184a, #800f2f)",
        "icon": "🕌",
        "season": "Oct – Mar (Mild Sunny)",
        "budget_from": "₹22,000",
        "tags": ["Amber Fort", "Bazaars", "Rajasthani Food", "Crafts"],
    },
    {
        "name": "Wayanad",
        "state": "Kerala, India",
        "tagline": "Pristine Western Ghats paradise — spice trails, wildlife, and waterfalls.",
        "image": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=700&q=80",
        "fallback_gradient": "linear-gradient(135deg, #023e8a, #0077b6)",
        "icon": "🌿",
        "season": "Oct – May (Post-Monsoon Lush)",
        "budget_from": "₹19,000",
        "tags": ["Wildlife", "Spice Hills", "Waterfalls", "Caves"],
    },
]


def render_destination_showcase(on_select_destination: Optional[Callable[[str], None]] = None) -> None:
    """Render curated destination cards with fallback protection and quick-select buttons."""
    render_html(
        """
        <div style="margin: 32px 0 16px 0;">
            <div class="spirit-hero-badge">
                <span>🌟</span> Trending Destinations
            </div>
            <h2 style="font-size: 1.85rem; margin-bottom: 6px;">Handpicked Havens for Your Next Journey</h2>
            <p style="color: #475569; font-size: 0.95rem; margin-bottom: 20px;">
                Explore top-rated Indian destinations, optimized for current season and climate.
                Click <strong>Select for Planning</strong> to populate your trip form instantly.
            </p>
        </div>
        """
    )

    cols = st.columns(3)
    for idx, dest in enumerate(FEATURED_DESTINATIONS):
        col = cols[idx % 3]
        with col:
            tags_html = "".join([f'<span class="dest-pill">{t}</span>' for t in dest["tags"]])
            card_html = f"""
            <div class="dest-card">
                <div class="dest-card-img-wrapper" style="background: {dest['fallback_gradient']};">
                    <img 
                        src="{dest['image']}" 
                        alt="{dest['name']}" 
                        class="dest-card-img" 
                        loading="lazy"
                        onerror="this.style.display='none'; this.parentElement.innerHTML='<div style=\\'display:flex;align-items:center;justify-content:center;height:100%;font-size:3rem;\\'>{dest['icon']}</div>';"
                    />
                    <div class="dest-card-badge">{dest['season']}</div>
                </div>
                <div class="dest-card-body">
                    <div>
                        <div style="display: flex; align-items: baseline; justify-content: space-between;">
                            <div class="dest-card-title">{dest['name']}</div>
                            <span style="font-size: 0.8rem; color: #64748B;">{dest['icon']}</span>
                        </div>
                        <div style="font-size: 0.78rem; color: #0284C7; margin-bottom: 6px; font-weight: 600;">{dest['state']}</div>
                        <div class="dest-card-tagline">{dest['tagline']}</div>

                        <div class="dest-card-tags">
                            {tags_html}
                        </div>
                    </div>
                    <div class="dest-card-footer">
                        <div>
                            <div class="dest-price-label">Typical Est.</div>
                            <div class="dest-price-value">{dest['budget_from']}</div>
                        </div>
                    </div>
                </div>
            </div>
            """
            render_html(card_html)
            
            # Interactive Streamlit button to immediately populate the form
            if st.button(f"🎯 Select {dest['name']}", key=f"btn_dest_{idx}", use_container_width=True):
                st.session_state.form_destination = dest["name"]
                st.session_state.undecided_destination = False
                st.rerun()
            render_html("<div style='margin-bottom: 20px;'></div>")
