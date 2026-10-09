# SpiritIQ — AI Travel Planning Agent

**SpiritIQ** is an autonomous AI travel planning agent engineered for rapid, intelligent travel orchestration. It discovers destinations, evaluates real-time Open-Meteo weather, calculates optimal routing via shortest-path graph algorithms (Dijkstra), compares multi-modal transit options, balances budgets in Indian Rupees (INR), and synthesizes day-by-day itineraries with safety precautions using Google Gemini AI.

---

## 1. System Architecture

SpiritIQ enforces strict separation of concerns between presentation and computation:

```text
spirit-iq-travel-agent/
├── frontend/                     # Streamlit User Interface
│   ├── app.py                    # Multi-tab dashboard & interactive input form
│   ├── components/               # Modular UI widgets
│   ├── pages/                    # Multi-page application views
│   └── README.md                 # Frontend guide
├── backend/                      # Pure Python Business Logic & AI
│   ├── __init__.py               # Package exports
│   ├── agent.py                  # Multi-step Gemini AI Agent Orchestrator (Member 1)
│   ├── schemas.py                # Pydantic v2 data models (contracts)
│   ├── config.py                 # Safe environment loader & key masking
│   ├── tools/                    # Specialized planning tools
│   │   ├── destination_tool.py   # Discovery & seasonal scoring (Member 2)
│   │   ├── weather_tool.py       # Open-Meteo weather & packing tips (Member 2)
│   │   ├── safety_tool.py        # Contextual safety advisories & helplines (Member 2)
│   │   ├── route_tool.py         # Route calculation & alternates (Member 3)
│   │   ├── dijkstra.py           # Dijkstra shortest path corridor engine (Member 3)
│   │   ├── transport_tool.py     # Multi-modal transit comparison (Member 3)
│   │   ├── budget_tool.py        # INR Budget breakdown, deficit audit (Member 3)
│   │   ├── itinerary_tool.py     # Day-wise itinerary construction (Member 4)
│   │   └── group_tool.py         # Group preference aggregation (Member 4)
│   ├── services/                 # External API client wrappers
│   │   ├── places_service.py     # Google Places API client (Member 2)
│   │   ├── weather_service.py    # Open-Meteo HTTP client with 16-day window (Member 2)
│   │   └── maps_service.py       # Google Routes & Maps client (Member 3)
│   └── README.md                 # Backend architectural documentation
├── tests/                        # Automated Test Suite (pytest)
│   ├── test_agent.py             # Agent workflow tests (Mocked Gemini)
│   ├── test_budget.py            # Budget allocation & deficit tests
│   ├── test_config.py            # Environment & secret masking tests
│   ├── test_destination.py       # Seasonal destination discovery tests
│   ├── test_dijkstra.py          # Dijkstra graph algorithm tests
│   ├── test_routes.py            # Route corridor & transit tests
│   ├── test_schemas.py           # Schema validation & serialization tests
│   └── test_weather.py           # Weather coordinate & forecast window tests
├── .env.example                  # Template configuration (no secrets)
├── .gitignore                    # Git exclusions (secrets, caches, venv)
├── requirements.txt              # Production and development dependencies
└── README.md                     # Root project guide
```

---

## 2. Four-Member Architecture Responsibilities

| Role | Member | Core Responsibilities | Key Files |
| :--- | :--- | :--- | :--- |
| **Member 1** | **Team Lead** | AI Multi-step Orchestration, Gemini API Integration, Schemas, Config, GitHub & Integration | `backend/agent.py`, `backend/schemas.py`, `backend/config.py` |
| **Member 2** | **Engineer** | Seasonal Destination Discovery, Open-Meteo Weather Service, Contextual Safety Advisories | `backend/tools/destination_tool.py`, `backend/tools/weather_tool.py`, `backend/tools/safety_tool.py`, `backend/services/weather_service.py` |
| **Member 3** | **Engineer** | Dijkstra Corridor Shortest Path, Transit Mode Comparison, Budget Breakdown & Deficit Audit | `backend/tools/dijkstra.py`, `backend/tools/route_tool.py`, `backend/tools/transport_tool.py`, `backend/tools/budget_tool.py` |
| **Member 4** | **Engineer** | Streamlit UI Dashboard, Form Controls, Multi-tab Results View, Session State Preservation | `frontend/app.py`, `frontend/components/`, `backend/tools/itinerary_tool.py`, `backend/tools/group_tool.py` |

---

## 3. Windows Setup & Quickstart

### Prerequisites
* Windows 10/11 with PowerShell
* Python 3.10+ installed (Python 3.12 recommended)
* Git installed

### Step 1: Clone Repository
```powershell
cd D:\Projects
git clone https://github.com/<your-org>/spirit-iq-travel-agent.git
cd spirit-iq-travel-agent
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate in PowerShell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the `.env.example` file to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` and provide your credentials:
```env
# Google Gemini API Key (Required for AI Orchestration)
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Google Gemini Model Name (Configurable: gemini-3.8-flash recommended)
GEMINI_MODEL=gemini-3.8-flash

# Google Maps API Key (Optional Places & Routes)
GOOGLE_MAPS_API_KEY=
```

> [!IMPORTANT]
> **API Key Security Protocol:**
> 1. NEVER commit your `.env` file to Git. Both `.env` and `.venv/` are strictly ignored by `.gitignore`.
> 2. NEVER paste API keys into chat prompts or commit messages.
> 3. Keys are masked automatically in code using `mask_secret()` and sanitized with `sanitize_text()`.

---

## 4. Running the Application

Launch the Streamlit frontend with:
```powershell
python -m streamlit run frontend/app.py
```
Open your browser at `http://localhost:8501`.

---

## 5. Running Automated Tests

SpiritIQ includes 37 automated tests covering schemas, destination selection, weather windows, routing corridors, budget audits, configuration masking, and agent orchestration.

All unit tests use mocked Gemini and external service responses, ensuring tests run offline without network access or secret exposure:
```powershell
# Run the entire test suite
python -m pytest tests/ -v

# Run individual test modules
python -m pytest tests/test_agent.py -v
python -m pytest tests/test_destination.py -v
python -m pytest tests/test_weather.py -v
python -m pytest tests/test_routes.py -v
python -m pytest tests/test_budget.py -v
python -m pytest tests/test_config.py -v
python -m pytest tests/test_schemas.py -v
```

---

## 6. Multi-Step Agent Planning Workflow

When a user submits a travel request:
1. **Validation:** Input dates, budget, traveller counts, and pace are validated against Pydantic models.
2. **Destination Discovery:** If unspecified, `destination_tool` scores destinations by travel month, budget, and interests.
3. **Weather Analysis:** `weather_service` queries Open-Meteo. Live forecast is served if within 16 days; seasonal guidance is served if beyond 16 days.
4. **Dijkstra Route Calculation:** `dijkstra.py` computes the shortest corridor path and alternative scenic routes across calibrated highway waypoints.
5. **Transit Comparison:** `transport_tool` benchmarks Flight, Train, Bus, and Cab travel times and fares.
6. **Budget Audit:** `budget_tool` computes per-person allocations and alerts if the budget is constrained.
7. **Contextual Safety:** `safety_tool` provides geography- and group-specific precautions and emergency numbers.
8. **Gemini Synthesis:** `agent.py` prompts Gemini with tool grounding to generate an enriched day-wise itinerary matching the strict `TripPlan` Pydantic schema.
