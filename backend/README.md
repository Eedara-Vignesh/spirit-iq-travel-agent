# SpiritIQ Backend Documentation

The `backend/` directory encapsulates all data models, environment configuration, external service integrations, algorithmic computation (Dijkstra routing and budget optimization), and the Groq AI agent orchestrator.

---

## 1. Directory Structure

```text
backend/
├── __init__.py             # Package exports (schemas, config)
├── agent.py                # AI Orchestrator & Groq caller (Member 1)
├── schemas.py              # Strict Pydantic v2 data models
├── config.py               # Safe environment loader with key masking
├── tools/                  # Granular modular tools
│   ├── destination_tool.py # Destination discovery (Member 2)
│   ├── weather_tool.py     # Open-Meteo weather analysis (Member 2)
│   ├── safety_tool.py      # Safety tips & helplines (Member 2)
│   ├── route_tool.py       # Primary & alternate route generation (Member 3)
│   ├── dijkstra.py         # Dijkstra shortest-path algorithm (Member 3)
│   ├── transport_tool.py   # Multi-modal transit comparison (Member 3)
│   ├── budget_tool.py      # Budget breakdown & validation (Member 3)
│   ├── itinerary_tool.py   # Day-wise itinerary construction (Member 4)
│   └── group_tool.py       # Group preference aggregation (Member 4)
└── services/               # External API client wrappers
    ├── places_service.py   # Google Places API client (Member 2)
    ├── weather_service.py  # Open-Meteo HTTP client (Member 2)
    └── maps_service.py     # Google Maps / Routes client (Member 3)
```

---

## 2. Core Schemas & Data Contracts

All data flowing between the frontend and backend is validated using Pydantic v2 in `backend/schemas.py`:

* **`TripRequest`**: Input submitted by the user.
  * Required: `origin`, `start_date`, `end_date`, `budget_inr`.
  * Optional / Defaults: `destination`, `trip_type` (solo, couple, family, friends, group), `num_travellers` (gt 0), `interests`, `pace` (relaxed, balanced, packed), `transport_preferences`, `is_flexible_dates`, `date_flexibility_days`.
  * Validation: Guarantees `end_date >= start_date`, `budget_inr > 0`, `num_travellers > 0`.
* **`ToolResult`**: Uniform envelope returned by all backend tools.
  * Fields: `success: bool`, `data: Any`, `error: Optional[str]`, `metadata: Dict[str, Any]`.
  * Constructors: `ToolResult.ok(data=...)` and `ToolResult.fail(error=...)`.
* **`TripPlan`**: Complete trip synthesis model consumed by the frontend.
  * Includes `destinations`, `itinerary` (list of `DayPlan`), `weather_summary`, `transport_options`, `budget_breakdown`, `safety_precautions`, `alternate_routes`, `booking_links`, and non-fatal `errors`.

---

## 3. Configuration & Security

Configuration is managed in `backend/config.py`:
* Reads from the project root `.env` via `python-dotenv`.
* Never exposes raw secrets in string formatting, logs, or exceptions (all outputs use `mask_secret()`).
* Access via `get_settings()`:
  ```python
  from backend.config import get_settings

  settings = get_settings()
  if settings.is_groq_configured:
      # Proceed with AI agent call
      pass
  ```

---

## 4. How to Develop & Test a Tool

When writing a new tool in `backend/tools/`:
1. Accept typed parameters.
2. Return a `ToolResult` instance using `ToolResult.ok(...)` or `ToolResult.fail(...)`.
3. Add a corresponding unit test in `tests/`.
4. Run tests:
   ```powershell
   pytest tests/
   ```
