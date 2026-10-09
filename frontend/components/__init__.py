"""
frontend/components package
Reusable UI components for SpiritIQ Travel Planner.
"""

from __future__ import annotations
import textwrap
import streamlit as st


def render_html(html_str: str) -> None:
    """
    Render application-authored HTML cleanly and safely.
    Uses st.html when available (Streamlit >= 1.38) to directly render DOM nodes
    without CommonMark 4-space code block escaping, with dedented st.markdown fallback.
    """
    cleaned = textwrap.dedent(html_str).strip()
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)
