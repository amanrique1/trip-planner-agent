import json
import re
import logging

from config import is_gemini_model
from google.adk.agents.callback_context import CallbackContext

from agents.utils.tools import (
    raw_get_coordinates,
    raw_get_weather,
    raw_duckduckgo_search,
)

logger = logging.getLogger("callbacks")


# ═══════════════════════════════════════════════════════════════════════
# Guard — shared by every local-only callback
# ═══════════════════════════════════════════════════════════════════════

def _skip_if_cloud(name: str) -> bool:
    """Return True when running a cloud model (callbacks not needed)."""
    if is_gemini_model():
        logger.debug(
            "%s: skipped — cloud model handles this via tool calls", name
        )
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════
# Intake — LOCAL only (parses LLM JSON output → individual state keys)
# ═══════════════════════════════════════════════════════════════════════

def store_trip_params(callback_context: CallbackContext) -> None:
    """
    after_agent_callback for IntakeAgent (local models).
    Reads the raw JSON the LLM wrote into state['trip_params_raw'],
    parses it, and fans out into the individual state keys the
    downstream agents expect.
    """
    if _skip_if_cloud("store_trip_params"):
        return None

    raw = callback_context.state.get("trip_params_raw", "")
    logger.debug("Raw intake output: %s", raw)

    match = re.search(r"\{[^}]+\}", raw, re.DOTALL)
    if not match:
        logger.warning("No JSON block found in intake output")
        return None

    try:
        params = json.loads(match.group())
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed: %s", exc)
        return None

    callback_context.state["origin"]      = params["origin"]
    callback_context.state["destination"] = params["destination"]
    callback_context.state["start_date"]  = params["start_date"]
    callback_context.state["end_date"]    = params["end_date"]
    callback_context.state["dates"]       = (
        f"{params['start_date']} to {params['end_date']}"
    )
    callback_context.state["trip_params_summary"] = (
        f"{params['origin']} → {params['destination']}, "
        f"{params['start_date']} to {params['end_date']}"
    )

    logger.info(
        "Stored trip params: %s",
        callback_context.state["trip_params_summary"],
    )
    return None


# ═══════════════════════════════════════════════════════════════════════
# Weather — LOCAL only (pre-fetches coordinates + forecast)
# ═══════════════════════════════════════════════════════════════════════

def prefetch_weather(callback_context: CallbackContext) -> None:
    if _skip_if_cloud("prefetch_weather"):
        return None

    destination = callback_context.state.get("destination", "")
    if not destination:
        logger.warning("No destination in state — skipping weather prefetch")
        callback_context.state["weather_prefetched"] = json.dumps(
            {"error": "destination is missing"}
        )
        return None

    coords = raw_get_coordinates(destination)
    if "error" in coords:
        callback_context.state["weather_prefetched"] = json.dumps(coords)
        return None

    weather = raw_get_weather(coords["lat"], coords["long"])

    if "error" not in weather:
        callback_context.state["weather_raw"] = {
            "daily_max":     weather["daily"]["temperature_2m_max"],
            "daily_min":     weather["daily"]["temperature_2m_min"],
            "weather_codes": weather["daily"]["weathercode"],
            "dates":         weather["daily"]["time"],
        }

    callback_context.state["weather_prefetched"] = json.dumps(
        weather, default=str
    )
    logger.info("Weather data pre-fetched for %s", destination)
    return None


# ═══════════════════════════════════════════════════════════════════════
# Flights — LOCAL only (pre-fetches search results)
# ═══════════════════════════════════════════════════════════════════════

def prefetch_flights(callback_context: CallbackContext) -> None:
    if _skip_if_cloud("prefetch_flights"):
        return None

    origin      = callback_context.state.get("origin", "")
    destination = callback_context.state.get("destination", "")
    dates       = callback_context.state.get("dates", "")

    if not origin or not destination:
        callback_context.state["flight_prefetched"] = json.dumps(
            {"error": "origin or destination is missing"}
        )
        return None

    query = f"flights from {origin} to {destination} {dates} prices airlines"
    results = raw_duckduckgo_search(query, max_results=8)

    callback_context.state["flight_prefetched"] = json.dumps(
        results, default=str
    )
    logger.info("Flight results pre-fetched for %s → %s", origin, destination)
    return None


# ═══════════════════════════════════════════════════════════════════════
# Activities — LOCAL only (pre-fetches attractions + restaurants)
# ═══════════════════════════════════════════════════════════════════════

def prefetch_activities(callback_context: CallbackContext) -> None:
    if _skip_if_cloud("prefetch_activities"):
        return None

    destination = callback_context.state.get("destination", "")
    if not destination:
        callback_context.state["activities_prefetched"] = json.dumps(
            {"error": "destination is missing"}
        )
        return None

    queries = [
        f"top attractions and tours in {destination}",
        f"best restaurants in {destination}",
    ]
    all_results = []
    for q in queries:
        all_results.extend(raw_duckduckgo_search(q, max_results=5))

    callback_context.state["activities_prefetched"] = json.dumps(
        all_results, default=str
    )
    logger.info("Activities results pre-fetched for %s", destination)
    return None


# ═══════════════════════════════════════════════════════════════════════
# Hotels — LOCAL only (pre-fetches hotel listings)
# ═══════════════════════════════════════════════════════════════════════

def prefetch_hotels(callback_context: CallbackContext) -> None:
    if _skip_if_cloud("prefetch_hotels"):
        return None

    destination = callback_context.state.get("destination", "")
    if not destination:
        callback_context.state["hotel_prefetched"] = json.dumps(
            {"error": "destination is missing"}
        )
        return None

    query = f"best rated hotels in {destination} with prices"
    results = raw_duckduckgo_search(query, max_results=8)

    callback_context.state["hotel_prefetched"] = json.dumps(
        results, default=str
    )
    logger.info("Hotel results pre-fetched for %s", destination)
    return None