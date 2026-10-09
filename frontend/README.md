# SpiritIQ Frontend Documentation

The `frontend/` directory houses the interactive Streamlit user interface for SpiritIQ, designed as an **Agent-First AI Travel Planning Workspace** with live pipeline execution tracing, activity reasoning logs, and resilient Gemini quota handling.
Assigned to: **Member 4 (Frontend, Itinerary and Group Planning)**

---

## 1. Directory Structure

```text
frontend/
├── app.py                      # Main application orchestrator & Agent-First Workspace
├── components/                 # Modular, reusable presentation components
│   ├── __init__.py             # render_html utility for safe DOM injection
│   ├── header.py               # Top brand navbar & engine status pills
│   ├── agent_workspace.py      # Real execution timeline, activity log & quota banner
│   ├── trip_form.py            # Travel Request Panel (6 organized sections & presets)
│   ├── itinerary_view.py       # Destination rationale & day-by-day activity timeline
│   ├── budget_view.py          # Expenditure audit, category progress bars & per-person metrics
│   ├── transit_view.py         # Modal benchmark matrix & Dijkstra highway corridor routes
│   ├── weather_safety_view.py  # Weather conditions, packing checklist & local safety advisories
│   └── footer.py               # Modern SaaS product footer
├── styles/
│   └── theme.css               # Midnight navy & electric teal design tokens, glassmorphism & resets
├── pages/                      # Multi-page extensions
└── README.md                   # This document
```

---

## 2. Agent-First Product Experience

- **Travel Request Panel**: Comprehensive input form with presets for popular Indian journeys (Goa, Coorg, Udaipur), flexible date tolerances (±2 days), traveller dynamics, pace, and accessibility preferences.
- **Agent Execution Timeline**: Real-time status indicators for each pipeline stage:
  1. Request Validation (Deterministic)
  2. Destination Discovery (Curated seasonal scoring)
  3. Weather Analysis (Live Open-Meteo API)
  4. Highway Corridor Routing (Weighted Dijkstra Graph)
  5. Transit Modal Comparison (Multimodal matrix)
  6. Budget Optimization (4-Tier deterministic model with buffer)
  7. Contextual Safety Advisories (Localized matrix)
  8. Gemini AI Synthesis (Gemini 3.8 Flash)
  9. Pydantic Schema Audit (Output contract validation)
- **Live Activity Log**: Transparent chronological stream of actual tool executions and evidence collected.
- **Quota Resilience**: When Gemini free-tier daily requests are exhausted (HTTP 429), the workspace displays a professional warning card linking to official documentation, preserves user inputs, and presents a transparent **Deterministic Tool Preview (Non-LLM)**.

---

## 3. Architecture Rules

1. **No API Secrets in Frontend:** The frontend never reads or handles raw API keys. All service keys reside in `backend/config.py` and remain on the server.
2. **Interface via Pydantic Schemas:** User input collected in UI forms is validated directly into `TripRequest` instances before invocation of `TravelPlanningAgent.plan_trip` or `plan_trip_stream`.
3. **No Heavy Business Logic:** Routing algorithms (Dijkstra), meteorological parsing (Open-Meteo), and LLM orchestration belong strictly in `backend/`.
4. **Transparent Provenance:** All displayed data explicitly cites its source (e.g. Open-Meteo live endpoint, Dijkstra corridor solver, deterministic budget engine, or Gemini AI).

---

## 4. Running the Frontend (Windows PowerShell)

```powershell
# Activate your virtual environment first
.\.venv\Scripts\Activate.ps1

# Launch the Streamlit application
streamlit run frontend/app.py
```
By default, the dashboard runs at `http://localhost:8501`.
