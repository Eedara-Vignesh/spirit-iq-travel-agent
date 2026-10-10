# SpiritIQ Frontend Documentation

The `frontend/` directory houses the interactive Streamlit user interface for SpiritIQ, enhanced with a premium travel-tech aesthetic, fluid CSS micro-animations, and JavaScript micro-interactions.
Assigned to: **Member 4 (Frontend, Itinerary and Group Planning)**

---

## 1. Directory Structure

```text
frontend/
├── app.py                      # Main application orchestrator & dashboard view
├── components/                 # Modular, reusable presentation components
│   ├── __init__.py
│   ├── header.py               # Top brand navbar & engine status pills
│   ├── hero.py                 # Cinematic hero with JS floating elements & metric counters
│   ├── destination_cards.py    # Curated destination cards with fallback images & quick-select
│   ├── features.py             # 4-step pipeline explanation & core feature cards
│   ├── trip_form.py            # 6-section organized travel preferences form with validation
│   ├── itinerary_view.py       # Day-by-day interactive timeline & activity cards
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

## 2. Design System & Tokens

- **Color Palette**: Midnight Navy (`#060B18`, `#0B132B`, `#111E38`), Electric Teal (`#00F0FF`, `#00C2CB`), Emerald Aqua (`#06D6A0`), Amber Gold (`#FFB703`), and Coral (`#FF5470`).
- **Typography**: Google Fonts `Outfit` (headings, display numbers) & `Plus Jakarta Sans` (body, forms).
- **Surfaces**: Frosted glassmorphism (`backdrop-filter: blur(14px)`), subtle translucent borders (`rgba(255,255,255,0.08)`), and soft radial glows.
- **Interactions**: Animated number tickers, floating travel iconography, smooth hover scale transitions, and native `prefers-reduced-motion` compliance.

---

## 3. Architecture Rules

1. **No API Secrets in Frontend:** The frontend never reads or handles raw API keys. All service keys reside in `backend/config.py` and remain on the server.
2. **Interface via Pydantic Schemas:** User input collected in UI forms is validated directly into `TripRequest` instances before invocation of `TravelPlanningAgent.plan_trip`.
3. **No Heavy Business Logic:** Routing algorithms (Dijkstra), meteorological parsing (Open-Meteo), and LLM orchestration belong strictly in `backend/`.
4. **Resilient Imagery:** All destination imagery uses reliable URLs paired with automatic SVG/CSS gradient fallbacks via `onerror` handlers to guarantee zero broken images.

---

## 4. Running the Frontend (Windows PowerShell)

```powershell
# Activate your virtual environment first
.\.venv\Scripts\Activate.ps1

# Launch the Streamlit application
streamlit run frontend/app.py
```
By default, the dashboard runs at `http://localhost:8501`.
