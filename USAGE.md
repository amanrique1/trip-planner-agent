# Usage Guide

This guide covers all three ways to interact with the Trip Planner.

---

## 0. Setup & Security

Before running the application, you must configure the environment and generate secure credentials.

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Generate a **SECRET_KEY** for JWT signing:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
3. Generate the **ADMIN_PASSWORD_HASH** for authentication:
   ```bash
   uv run scripts/hash_creator.py
   ```
   This interactive script will prompt for a password and provide the bcrypt hash to paste into your `.env` file.

---

## 1. REST API

### Start the server

```bash
uv run trip-planner-api
# or
uv run uvicorn api.app:application --host 0.0.0.0 --port 8000 --reload
```

Interactive docs: **http://localhost:8000/docs**

---

### Step 1 — Obtain a JWT token

```bash
curl -X POST http://localhost:8000/auth/token \
  -u admin:your_password
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_minutes": 60
}
```

---

### Step 2 — Plan a trip

```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST http://localhost:8000/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Plan a 5-day trip to Paris departing from Bucaramanga, Colombia."
  }'
```

**Response:**

```json
{
  "request_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "session_id": "a1b2c3d4-...",
  "itinerary": "# Your Paris Trip Plan\n\n## Weather Overview\n...",
  "latency_ms": 12450.3
}
```

**Resume a session:**

```bash
curl -X POST http://localhost:8000/plan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What if I want to extend the trip by 2 days?",
    "session_id": "a1b2c3d4-..."
  }'
```

---

### Health check

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

### Rate limiting behaviour

When you exceed 10 requests / 60 seconds you receive:

```json
HTTP 429 Too Many Requests
Retry-After: 42

{
  "detail": "Rate limit exceeded. Retry after 42 seconds."
}
```

---

## 2. CLI

### Standard usage

```bash
uv run trip-planner
```

This starts the **Interactive REPL**. You can talk to the agent in natural language, and it will maintain session state across your questions.

```
╭──────────────────────────────────────╮
│  Trip Planner Agent                  │
│  Your AI assistant for planning...   │
╰──────────────────────────────────────╯

How can I help you plan your trip? (type 'exit' to quit)
You: Plan a trip to Paris from New York.
```

```
╭──────────────────────────────────────╮
│  Trip Planner — Interactive Mode     │
╰──────────────────────────────────────╯
Type exit or quit to leave.

You: Plan a trip to Amsterdam from Buenos Aires
⠸ Planning your trip…

# Your Amsterdam Trip Plan
...

You: Can you suggest vegetarian restaurants near those activities?
...
```

### CLI help

```bash
uv run trip-planner --help
uv run trip-planner plan --help
uv run trip-planner interactive --help
```

---

## 3. ADK Web UI

The `root_agent` export in `src/agents/trip_agent.py` is automatically discovered by the ADK developer UI.

```bash
# Shortcut command
uv run trip-planner-web

# Or manual command from the project root
uv run adk web src
```

Then open **http://localhost:8080** in your browser.

The ADK web UI lets you:
- Chat with the agent interactively
- Inspect the full event stream (tool calls, sub-agent outputs)
- View session state (weather_info, flight_info, etc.)
- Replay and debug individual steps

> **Note:** The ADK web UI does **not** apply the security filters or rate limiter.
> It is intended for development and debugging only. Never expose it publicly.

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | — | **Required.** Gemini + Search API key |
| `SECRET_KEY` | — | **Required in prod.** 32-byte hex JWT signing key |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT lifetime |
| `RATE_LIMIT_REQUESTS` | `10` | Max requests per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate-limit window |
| `MAX_INPUT_LENGTH` | `1000` | Max characters in user input |
| `MAX_OUTPUT_LENGTH` | `50000` | Max characters in agent output |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FILE` | `logs/audit.jsonl` | Path to JSON Lines audit log |
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `8000` | API port |
| `ADMIN_USERNAME` | `admin` | Default admin username |
| `ADMIN_PASSWORD_HASH` | — | **Required.** bcrypt hash of admin password |

---

## Audit Log Format

Every request is logged to `logs/audit.jsonl` as a JSON object:

```json
{"event": "request_received",  "request_id": "...", "username": "admin", "endpoint": "/plan", "user_input": "Plan a trip...", "timestamp": "2024-07-01T12:00:00Z", "level": "info"}
{"event": "request_completed", "request_id": "...", "username": "admin", "status": "success", "output_preview": "# Your Paris...", "latency_ms": 12340.5, "timestamp": "2024-07-01T12:00:12Z", "level": "info"}
```

Security events (blocked inputs, sanitized outputs, rate limits) use `"event": "security_event"` with `"level": "warning"`.