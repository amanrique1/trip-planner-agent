# 🌍 Trip Planner — AI-Powered Travel Assistant

A production-grade travel planning agent built with **Google ADK**, **Gemini 2.5 Flash**,
and a full security stack. It orchestrates parallel and sequential agent phases to
deliver weather-aware itineraries with flights, activities, and hotels.

---

## Architecture

```
User Input
    │
    ▼
┌──────────────────────────────────────┐
│         Security Layer               │
│  Input Filter → Rate Limiter         │
│  Audit Logger ← Output Filter        │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────┐
│            TripPlanner (Sequential)                │
│                                                    │
│  Phase 0 — IntakeAgent                             │
│    └→ save_trip_params (tool_context.state)        │
│       writes: origin, destination, dates           │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │ Phase 1 — Parallel                           │  │
│  │  ├─ WeatherAgent   reads {destination}       │  │
│  │  │   ├→ get_coordinates (plain return)       │  │
│  │  │   └→ get_weather (tool_context.state)     │  │
│  │  │      writes: weather_raw                  │  │
│  │  │                                           │  │
│  │  └─ FlightAgent    reads {origin}            │  │
│  │      └→ google_search  {destination},{dates} │  │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  Phase 2 — ActivitiesAgent                         │
│    reads {destination},{weather_raw},{weather_info}│
│    └→ google_search                                │
│                                                    │
│  Phase 3 — HotelAgent                              │
│    reads {destination},{activities_info}           │
│    └→ google_search                                │
│                                                    │
│  Phase 4 — SummaryAgent                            │
│    reads all state keys → final Markdown plan      │
└────────────────────────────────────────────────────┘
```

### State Flow

Agents communicate through **session state** rather than passing the full
conversation history. Each agent reads only the specific keys it needs and
writes its output to a dedicated key.

```
IntakeAgent (save_trip_params → tool_context.state)
│
│  state["origin"]       = "New York"
│  state["destination"]  = "Paris"
│  state["start_date"]   = "2025-06-10"
│  state["end_date"]     = "2025-06-17"
│  state["dates"]        = "2025-06-10 to 2025-06-17"
│
├── WeatherAgent  reads {destination}, {dates}
│   ├→ get_coordinates  → plain dict return (no state)
│   ├→ get_weather      → tool_context.state["weather_raw"]
│   └→ output_key       → state["weather_info"]
│
├── FlightAgent   reads {origin}, {destination}, {dates}
│   └→ output_key       → state["flight_info"]
│
ActivitiesAgent   reads {destination}, {dates}, {weather_raw}, {weather_info}
│   └→ output_key       → state["activities_info"]
│
HotelAgent        reads {destination}, {dates}, {activities_info}
│   └→ output_key       → state["hotel_info"]
│
SummaryAgent      reads all keys
    └→ output_key       → state["final_itinerary"]
```

### Agent Pipeline

| Phase | Agent | Reads from state | Writes to state | Tools |
|-------|-------|-----------------|----------------|-------|
| 0 | IntakeAgent | user message | `origin`, `destination`, `dates`, `start_date`, `end_date` | `save_trip_params` |
| 1a (parallel) | WeatherAgent | `destination`, `dates` | `weather_info`, `weather_raw` | `get_coordinates`, `get_weather` |
| 1b (parallel) | FlightAgent | `origin`, `destination`, `dates` | `flight_info` | `google_search` |
| 2 | ActivitiesAgent | `destination`, `dates`, `weather_raw`, `weather_info` | `activities_info` | `google_search` |
| 3 | HotelAgent | `destination`, `dates`, `activities_info` | `hotel_info` | `google_search` |
| 4 | SummaryAgent | all above | `final_itinerary` | — |

### Tools & State Strategy

| Tool | State interaction | Rationale |
|------|------------------|-----------|
| `save_trip_params` | **Writes** via `tool_context.state` | Structured parameters parsed from natural language, reused by every downstream agent |
| `get_coordinates` | **Plain return** (no state) | Ephemeral lookup consumed only by `get_weather` within the same agent turn |
| `get_weather` | **Writes** `weather_raw` via `tool_context.state` | Structured API data (arrays of temps, codes, dates) needed by ActivitiesAgent for indoor/outdoor logic |
| `google_search` | No state | Results are synthesised into prose by each agent's `output_key` |

### Security Stack

| Layer | Implementation |
|-------|---------------|
| **Input filter** | Regex-based prompt injection detection + length limits |
| **Output filter** | PII / secret scanning with redaction fallback |
| **Rate limiting** | Sliding-window per-user (in-memory; swap to Redis for multi-node) |
| **Audit logging** | Structured JSON Lines via `structlog` → `logs/audit.jsonl` |
| **API auth** | HTTP Basic → JWT Bearer token (OAuth2 password flow) |

---

## Quick Start

### 1. Prerequisites

- Python **3.12+**
- [`uv`](https://github.com/astral-sh/uv) installed
- Google API key with Gemini + Search access

### 2. Clone & install

```bash
git clone https://github.com/amanrique1/trip-planner-agent.git
cd trip-planner-agent
uv sync
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env — set GOOGLE_API_KEY and generate SECRET_KEY + ADMIN_PASSWORD_HASH
```

Generate a **SECRET_KEY** (32-byte hex):

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Generate the **ADMIN_PASSWORD_HASH** (bcrypt):

```bash
uv run scripts/hash_creator.py
```

---

## Project Structure

```
src/
├── agents/
│   ├── tools.py              # save_trip_params, get_coordinates, get_weather
│   ├── intake_agent.py       # Extracts trip params → state
│   ├── weather_agent.py      # Coordinates + forecast
│   ├── flight_agent.py       # Google Search for flights
│   ├── activities_agent.py   # Weather-aware activity planning
│   ├── hotel_agent.py        # Activity-aware hotel search
│   └── trip_planner.py       # SequentialAgent orchestrator + Runner
├── api/
│   ├── app.py                # FastAPI application factory
│   ├── auth.py               # JWT authentication
│   ├── models.py             # Pydantic request/response models
│   └── routes.py             # /plan, /health, /auth endpoints
├── cli/
│   └── main.py               # Typer/Rich interactive REPL
├── security/
│   ├── filters.py            # Input/output filtering + sanitisation
│   ├── rate_limiter.py       # Sliding-window rate limiter
│   └── audit.py              # Structured JSON Lines logger
└── config.py                 # Pydantic-settings configuration

tests/
├── L1_components/            # Unit tests (mocked, fast, no LLM calls)
│   ├── test_tools.py         # get_coordinates, get_weather, save_trip_params
│   ├── test_auth.py          # Token generation + validation
│   ├── test_guardrails.py    # Input/output filters + rate limiter
│   ├── test_health.py        # Health endpoint
│   ├── test_parsers_formatters.py  # Pydantic model validation
│   └── test_plan.py          # /plan endpoint (mocked runner)
└── L2_tool_integration/      # Trajectory tests (real LLM calls)
    ├── trajectory.py         # Trajectory recorder + analysis utilities
    ├── test_intake_agent_trajectory.py
    ├── test_weather_agent_trajectory.py
    ├── test_flight_agent_trajectory.py
    ├── test_activities_agent_trajectory.py
    └── test_hotel_agent_trajectory.py

adk-app/
└── trip_planner/
    └── __init__.py           # ADK web UI entry point (exports root_agent)
```

---

## Architectural decisions

### Session State vs Conversation History

This project uses **session state** for inter-agent communication instead
of passing the full conversation to every agent. Each agent sees only the
state keys injected into its instruction via `{key}` template variables.

**Benefits:**

- **Reduced token usage** — each agent receives a minimal, focused context
- **Deterministic data flow** — explicit read/write contracts per agent
- **Structured data** — tools write machine-readable dicts (e.g. `weather_raw`)
  alongside the LLM's prose summaries (e.g. `weather_info`)

| Mechanism | What it stores | Who writes | Who reads |
|-----------|---------------|------------|-----------|
| `output_key` | Agent's prose summary | LLM (automatic) | Downstream agents via `{key}` |
| `tool_context.state` | Structured API data | Tool function (explicit) | Downstream agents via `{key}` |
| Session seed | Trip parameters | IntakeAgent's tool | Every agent |


---

## Testing

```bash
# All tests
uv run pytest

# L1 only — fast, no API keys needed
uv run pytest tests/L1_components

# L2 only — requires GOOGLE_API_KEY
uv run pytest tests/L2_tool_integration

# Single test file
uv run pytest tests/L1_components/test_tools.py

# Single test class
uv run pytest tests/L2_tool_integration/test_weather_agent_trajectory.py::TestWeatherToolSelection

# With verbose output
uv run pytest -v tests/L2_tool_integration/test_intake_agent_trajectory.py
```

### Test Levels

| Level | Scope | LLM calls | Speed | What it validates |
|-------|-------|-----------|-------|-------------------|
| **L1** | Unit / component | None (mocked) | Fast (~seconds) | Tools return correct data, state is written, API endpoints work, security filters block bad input |
| **L2** | Agent trajectory | Real Gemini calls | Slower (~30s per agent) | Correct tool selection, argument quality, call ordering, output relevance, no cross-agent tool leakage |

---

## Development

```bash
# Lint
uv run ruff check src tests

# Type-check
uv run mypy src
```

---

## Further Reading

See **[USAGE.md](USAGE.md)** for detailed instructions on all three
interfaces (REST API, CLI, and ADK web UI).