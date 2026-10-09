"""
frontend/components/agent_workspace.py
======================================
Agent Workspace presentation components:
1. Live execution timeline with real backend status and provenance
2. Chronological agent activity & reasoning summary log
3. Professional Gemini quota-exhaustion banner with rate-limit documentation link
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import streamlit as st

from backend.schemas import (
    AgentExecutionTrace,
    AgentStageRecord,
    StageStatus,
)
from frontend.components import render_html


def render_agent_timeline(trace: Optional[AgentExecutionTrace]) -> None:
    """Render the real multi-stage agent execution timeline with authentic statuses."""
    if not trace or not trace.stages:
        return

    status_config = {
        StageStatus.COMPLETED: {
            "icon": "✅",
            "color": "#06D6A0",
            "bg": "rgba(6, 214, 160, 0.12)",
            "border": "rgba(6, 214, 160, 0.3)",
            "label": "COMPLETED",
        },
        StageStatus.RUNNING: {
            "icon": "⚡",
            "color": "#00F0FF",
            "bg": "rgba(0, 240, 255, 0.15)",
            "border": "rgba(0, 240, 255, 0.4)",
            "label": "RUNNING",
        },
        StageStatus.SKIPPED: {
            "icon": "⏭️",
            "color": "#94A3B8",
            "bg": "rgba(148, 163, 184, 0.1)",
            "border": "rgba(148, 163, 184, 0.25)",
            "label": "SKIPPED",
        },
        StageStatus.FAILED: {
            "icon": "⚠️",
            "color": "#FF5470",
            "bg": "rgba(255, 84, 112, 0.12)",
            "border": "rgba(255, 84, 112, 0.35)",
            "label": "FAILED",
        },
        StageStatus.PENDING: {
            "icon": "⏳",
            "color": "#64748B",
            "bg": "rgba(100, 116, 139, 0.08)",
            "border": "rgba(100, 116, 139, 0.2)",
            "label": "PENDING",
        },
    }

    cards_html = []
    for stage in trace.stages:
        cfg = status_config.get(stage.status, status_config[StageStatus.PENDING])
        
        prov_badge = (
            f'<span style="font-size: 0.72rem; padding: 2px 8px; border-radius: 999px; background: rgba(0, 240, 255, 0.08); border: 1px solid rgba(0, 240, 255, 0.2); color: #00F0FF;">{stage.provenance}</span>'
            if stage.provenance
            else ""
        )
        
        duration_badge = (
            f'<span style="font-size: 0.72rem; color: #64748B;">({stage.duration_ms:.0f} ms)</span>'
            if stage.duration_ms is not None
            else ""
        )

        detail_text = stage.summary or stage.error or ("Awaiting execution..." if stage.status == StageStatus.PENDING else "")

        cards_html.append(
            f"""
            <div style="
                background: rgba(16, 28, 58, 0.6);
                border: 1px solid {cfg['border']};
                border-radius: 12px;
                padding: 12px 16px;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 12px;
            ">
                <div style="display: flex; align-items: center; gap: 10px; flex: 1;">
                    <span style="font-size: 1.15rem;">{cfg['icon']}</span>
                    <div>
                        <div style="font-size: 0.92rem; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 8px;">
                            <span>{stage.name}</span>
                            {prov_badge}
                            {duration_badge}
                        </div>
                        <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 2px;">
                            {detail_text}
                        </div>
                    </div>
                </div>
                <div style="
                    font-size: 0.72rem;
                    font-weight: 700;
                    letter-spacing: 0.05em;
                    padding: 3px 10px;
                    border-radius: 999px;
                    background: {cfg['bg']};
                    border: 1px solid {cfg['border']};
                    color: {cfg['color']};
                    white-space: nowrap;
                ">
                    {cfg['label']}
                </div>
            </div>
            """
        )

    render_html(
        f"""
        <div style="margin: 16px 0 20px 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <div style="font-size: 0.85rem; font-weight: 700; color: #00F0FF; text-transform: uppercase; letter-spacing: 0.06em;">
                    ⚡ Agent Orchestration Timeline
                </div>
                <div style="font-size: 0.75rem; color: #64748B;">
                    Model: <strong style="color: #F1F5F9;">{trace.model_used or 'Configured Gemini'}</strong>
                </div>
            </div>
            {''.join(cards_html)}
        </div>
        """
    )


def render_activity_log(activity_log: List[str]) -> None:
    """Render authentic chronological agent activity reasoning log."""
    if not activity_log:
        return

    log_items = []
    for line in activity_log:
        log_items.append(
            f"""<div style="font-family: 'Courier New', monospace; font-size: 0.78rem; color: #94A3B8; padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.03);">{line}</div>"""
        )

    render_html(
        f"""
        <div style="
            background: rgba(6, 11, 24, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 20px;
        ">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 0.78rem; font-weight: 700; color: #00F0FF; text-transform: uppercase; letter-spacing: 0.05em;">
                    📋 Agent Activity Log ({len(activity_log)} events)
                </span>
                <span style="font-size: 0.72rem; color: #06D6A0;">● Live Execution</span>
            </div>
            <div style="max-height: 180px; overflow-y: auto;">
                {''.join(log_items)}
            </div>
        </div>
        """
    )


def render_quota_exhausted_banner(quota_details: Optional[Dict[str, Any]] = None) -> None:
    """
    Render a clean, professional Gemini quota error alert without dumping raw JSON,
    linking to official rate-limits documentation.
    """
    model_name = quota_details.get("model", "gemini-3.8-flash") if quota_details else "gemini-3.8-flash"
    retry_sec = quota_details.get("retry_after") if quota_details else None
    retry_text = (
        f"Recommended retry interval: approximately <strong>{retry_sec} seconds</strong>."
        if retry_sec
        else "Please verify your project quota reset timing or configure a billing-enabled API key."
    )

    render_html(
        f"""
        <div style="
            background: linear-gradient(135deg, rgba(35, 18, 28, 0.9) 0%, rgba(45, 22, 22, 0.85) 100%);
            border: 1px solid rgba(255, 84, 112, 0.4);
            border-left: 4px solid #FF5470;
            border-radius: 14px;
            padding: 20px 24px;
            margin-bottom: 24px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        ">
            <div style="display: flex; align-items: baseline; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 1.3rem;">⚠️</span>
                <h3 style="font-size: 1.2rem; color: #FF5470; margin: 0;">
                    Gemini API Quota Limit Reached (HTTP 429 RESOURCE_EXHAUSTED)
                </h3>
            </div>

            <p style="font-size: 0.88rem; color: #F1F5F9; line-height: 1.5; margin-bottom: 12px;">
                The configured Gemini model (<code>{model_name}</code>) has exhausted its daily free-tier request quota.
                {retry_text}
            </p>

            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <a href="https://ai.google.dev/gemini-api/docs/rate-limits" target="_blank" style="
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    padding: 6px 14px;
                    border-radius: 8px;
                    background: rgba(255, 84, 112, 0.15);
                    border: 1px solid rgba(255, 84, 112, 0.35);
                    color: #FF5470;
                    text-decoration: none;
                    font-size: 0.8rem;
                    font-weight: 600;
                ">
                    🔗 View Google Gemini Rate Limits Documentation ↗
                </a>
                <span style="font-size: 0.78rem; color: #94A3B8;">
                    Inputs are preserved. You can adjust parameters or retry at any time.
                </span>
            </div>
        </div>
        """
    )
