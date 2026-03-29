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
┌──────────────────────────────────────┐
│         TripPlanner (Sequential)     │
│                                      │
│  ┌─────────────────────────────────┐ │
│  │ Phase 1 — Parallel              │ │
│  │  ├─ WeatherAgent                │ │
│  │  └─ FlightAgent                 │ │
│  └─────────────────────────────────┘ │
│  Phase 2 — ActivitiesAgent           │
│  Phase 3 — HotelAgent                │
│  Phase 4 — SummaryAgent              │
└──────────────────────────────────────┘
```

### Agent Pipeline

| Phase | Agent | Depends on | Output key |
|-------|-------|-----------|------------|
| 1a (parallel) | WeatherAgent | – | `weather_info` |
| 1b (parallel) | FlightAgent | – | `flight_info` |
| 2 | ActivitiesAgent | `weather_info` | `activities_info` |
| 3 | HotelAgent | `activities_info` | `hotel_info` |
| 4 | SummaryAgent | all above | `final_itinerary` |

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
git clone https://github.com/your-org/trip-planner.git
cd trip-planner
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
# Recommended: use the included interactive script
uv run scripts/hash_creator.py
```

---

## Running the Project

See **[USAGE.md](USAGE.md)** for detailed usage instructions for all three interfaces.

---

## Project Structure

src/
├── agents/           # Agent definitions (root_agent exported in trip_agent.py)
│   ├── trip_agent.py
│   ├── weather_agent.py
│   └── ...
├── api/              # FastAPI application
│   ├── app.py        # Application factory & entry point
│   ├── auth.py       # JWT authentication
│   └── routes.py     # API endpoints
├── cli/              # Interactive CLI
│   └── main.py       # Typer/Rich REPL
├── security/         # Filters, rate limiter, and audit logging
└── config.py         # Pydantic-settings configuration

---

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check src tests

# Type-check
uv run mypy src
```