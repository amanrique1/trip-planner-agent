# Usage Guide

Trip Planner provides three interfaces. All three share the same agent
pipeline and security stack.

---

## 1. REST API (FastAPI)

### Start the server

```bash
uv run trip-planner-api
# or
uv run uvicorn api.app:application --host 0.0.0.0 --port 8000 --reload
```

### Authenticate

```bash
curl -X POST http://localhost:8000/auth/token \
  -u admin:admin_pass
```

```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in_minutes": 60
}
```

### Plan a trip

```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST http://localhost:8000/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Plan a 7-day trip from New York to Paris, June 10-17"}'
```

The query is natural language. The **IntakeAgent** extracts origin,
destination, and dates automatically. All of these are valid:

```json
{"query": "Plan a 7-day trip from New York to Paris, June 10-17"}
{"query": "I want to visit Tokyo next week, flying from London"}
{"query": "Weekend getaway from SF to LA"}
```

### Response

```json
{
  "request_id": "abc-123",
  "session_id": "sess-456",
  "itinerary": "# Trip: New York → Paris\n\n## Weather\n...",
  "latency_ms": 12450.3
}
```

The `itinerary` field contains the full Markdown plan compiled by the
SummaryAgent from all five agent phases.

### Resume a session

Pass the `session_id` from a previous response to continue the
conversation with prior state intact:

```bash
curl -X POST http://localhost:8000/plan \
  -H "Authorization: Bearer eyJhbG..." \
  -H "Content-Type: application/json" \
  -d '{"query": "Add a day trip to Versailles", "session_id": "sess-456"}'
```

### Health check

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

### Error responses

| Status | Meaning |
|--------|---------|
| 400 | Input filter rejected the query (injection / length) |
| 401 | Missing or invalid JWT token |
| 422 | Pydantic validation failed (query too short / too long) |
| 429 | Rate limit exceeded — check `Retry-After` header |
| 500 | Internal error during agent execution |

---

## 2. Interactive CLI

### Start the REPL

```bash
uv run trip-planner
```
This starts the **Interactive REPL**. You can talk to the agent in natural language, and it will maintain session state across your questions.

### Example session

```
🌍 Trip Planner CLI
╭──────────────────────────────────────────────────────╮
│  Trip Planner Agent                                  │
│ Your AI assistant for planning the perfect journey.  │
╰──────────────────────────────────────────────────────╯

How can I help you plan your trip? (type 'exit' to quit)

You: Plan a trip from San Francisco to Tokyo, July 1-10

⏳ Planning your trip...

━━━ Phase 0: IntakeAgent ━━━
✓ Extracted: San Francisco → Tokyo, 2025-07-01 to 2025-07-10

━━━ Phase 1: Weather + Flights (parallel) ━━━
✓ Weather: Tokyo — highs 28-32°C, rainy season, pack umbrella
✓ Flights: 3 options found from $680

━━━ Phase 2: ActivitiesAgent ━━━
✓ 10 activities planned (indoor alternatives on rainy days)

━━━ Phase 3: HotelAgent ━━━
✓ 3 hotels recommended near activity clusters

━━━ Phase 4: SummaryAgent ━━━

# Trip: San Francisco → Tokyo
## July 1-10, 2025
...

You: quit
👋 Goodbye!
```

---

## 3. ADK Web UI

Google ADK provides a built-in web interface for testing agents
interactively.

### Start the UI

```bash
uv run adk web adk-app/
```

This opens a browser UI at `http://localhost:8080` where you can:

- Select the **trip_planner** agent from the dropdown
- Type natural language queries
- Watch each agent phase execute in real time
- Inspect the session state after each step
- See tool calls and their arguments / responses

### Example interaction

```
You: Plan a trip from Berlin to Barcelona, September 5-12

[IntakeAgent] → save_trip_params(
    origin="Berlin", destination="Barcelona",
    start_date="2025-09-05", end_date="2025-09-12"
)

[WeatherAgent] → get_coordinates(city="Barcelona")
               → get_weather(lat=41.39, long=2.17)

[FlightAgent]  → google_search("flights Berlin to Barcelona September 2025")

[ActivitiesAgent] → google_search("top things to do Barcelona September")

[HotelAgent] → google_search("hotels near Gothic Quarter Barcelona")

[SummaryAgent] → Final Markdown itinerary
```

---

## How the Pipeline Works

When you send a query through any interface, the same pipeline executes:

```
"Plan a trip from NYC to Paris, June 10-17"
                    │
                    ▼
┌─── IntakeAgent ──────────────────────────────────────┐
│  LLM parses natural language                         │
│  Calls save_trip_params → writes to session state:   │
│    origin="New York", destination="Paris"            │
│    dates="2025-06-10 to 2025-06-17"                  │
└──────────────────────────────────────────────────────┘
                    │
                    ▼
┌─── Parallel ─────────────────────────────────────────┐
│  WeatherAgent                                        │
│    reads state: {destination}, {dates}               │
│    get_coordinates("Paris") → lat=48.85, long=2.35   │
│    get_weather(48.85, 2.35) → writes {weather_raw}   │
│    output_key → writes {weather_info}                │
│                                                      │
│  FlightAgent                                         │
│    reads state: {origin}, {destination}, {dates}     │
│    google_search → writes {flight_info}              │
└──────────────────────────────────────────────────────┘
                    │
                    ▼
┌─── ActivitiesAgent ──────────────────────────────────┐
│  reads: {destination}, {dates},                      │
│         {weather_raw}, {weather_info}                │
│  Uses weather codes for indoor/outdoor decisions     │
│  google_search → writes {activities_info}            │
└──────────────────────────────────────────────────────┘
                    │
                    ▼
┌─── HotelAgent ───────────────────────────────────────┐
│  reads: {destination}, {dates}, {activities_info}    │
│  Finds hotels near activity clusters                 │
│  google_search → writes {hotel_info}                 │
└──────────────────────────────────────────────────────┘
                    │
                    ▼
┌─── SummaryAgent ─────────────────────────────────────┐
│  reads: ALL state keys                               │
│  Compiles polished Markdown itinerary                │
│  Adds packing tips based on weather                  │
│  writes {final_itinerary}                            │
└──────────────────────────────────────────────────────┘
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | No (OPT 1) | Gemini + Google Search API key |
| `LITELLM_MODEL` | No (OPT 2) | Model to use for the agent, instead of GOOGLE_API_KEY |
| `SECRET_KEY` | Yes | 32-byte hex string for JWT signing |
| `ADMIN_PASSWORD_HASH` | Yes | bcrypt hash of the admin password |
| `ADMIN_USERNAME` | No | Defaults to `admin` |
| `RATE_LIMIT_REQUESTS` | No | Max requests per window (default: 10) |
| `RATE_LIMIT_WINDOW` | No | Window size in seconds (default: 60) |
| `MAX_INPUT_LENGTH` | No | Max query length in chars (default: 5000) |

---

## Audit Log Format

Every request is logged to `logs/audit.jsonl` as a JSON object:

```json
{"event": "request_received",  "request_id": "...", "username": "admin", "endpoint": "/plan", "user_input": "Plan a trip...", "timestamp": "2024-07-01T12:00:00Z", "level": "info"}
{"event": "request_completed", "request_id": "...", "username": "admin", "status": "success", "output_preview": "# Your Paris...", "latency_ms": 12340.5, "timestamp": "2024-07-01T12:00:12Z", "level": "info"}
```

Security events (blocked inputs, sanitized outputs, rate limits) use `"event": "security_event"` with `"level": "warning"`.