import requests
import logging

from config import is_gemini_model
from duckduckgo_search import DDGS
from google.adk.tools import FunctionTool, ToolContext

logger = logging.getLogger("tools")


# ═══════════════════════════════════════════════════════════════════════
# RAW FUNCTIONS — no ToolContext, callable from callbacks or anywhere
# ═══════════════════════════════════════════════════════════════════════

def raw_duckduckgo_search(query: str, max_results: int = 5) -> list[dict]:
    """Search DuckDuckGo and return a list of result dicts."""
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)
        return [{"error": str(exc)}]


def raw_get_coordinates(city: str) -> dict:
    """Geocode *city* → {lat, long, name} or {error}."""
    try:
        clean_city = city.split(",")[0].strip()
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": clean_city, "count": 1},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "results" in data and data["results"]:
            r = data["results"][0]
            return {
                "lat":  r["latitude"],
                "long": r["longitude"],
                "name": r["name"],
            }
        return {"error": f"No results for '{city}'"}
    except requests.RequestException as exc:
        return {"error": f"Geocoding failed: {exc}"}


def raw_get_weather(lat: float, long: float) -> dict:
    """7-day forecast → full Open-Meteo JSON or {error}."""
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": long,
                "current_weather": True,
                "daily": "temperature_2m_max,temperature_2m_min,weathercode",
                "timezone": "auto",
                "forecast_days": 7,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        return {"error": f"Weather request failed: {exc}"}


# ═══════════════════════════════════════════════════════════════════════
# TOOL-WRAPPED VERSIONS — only used when cloud models call tools
# ═══════════════════════════════════════════════════════════════════════

def _duckduckgo_search_tool(query: str, max_results: int = 5) -> list[dict]:
    """Search DuckDuckGo for the given query."""
    return raw_duckduckgo_search(query, max_results)


def _get_coordinates_tool(city: str) -> dict:
    """
    Look up latitude and longitude for a given city name.

    Args:
        city: Name of the city, e.g. 'San Francisco'

    Returns:
        dict with lat, long, and resolved name, or an error key.
    """
    return raw_get_coordinates(city)


def _get_weather_tool(
    lat: float, long: float, tool_context: ToolContext
) -> dict:
    """
    Fetch a 7-day weather forecast for given coordinates.

    Args:
        lat:  Latitude of the location.
        long: Longitude of the location.

    Returns:
        JSON weather response with daily highs, lows, and weather codes.
    """
    data = raw_get_weather(lat, long)
    if "error" not in data:
        tool_context.state["weather_raw"] = {
            "daily_max":     data["daily"]["temperature_2m_max"],
            "daily_min":     data["daily"]["temperature_2m_min"],
            "weather_codes": data["daily"]["weathercode"],
            "dates":         data["daily"]["time"],
        }
    return data


def _save_trip_params_tool(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    tool_context: ToolContext,
) -> dict:
    """
    Persist the four trip parameters into session state.

    Args:
        origin:      Departure city.
        destination: Arrival city.
        start_date:  YYYY-MM-DD.
        end_date:    YYYY-MM-DD.

    Returns:
        Confirmation dict.
    """
    if "origin" in tool_context.state:
        tool_context.actions.escalate = True
        return {
            "status":  "already_saved",
            "message": "Trip parameters were already saved.",
        }

    params = {
        "origin":      origin,
        "destination": destination,
        "start_date":  start_date,
        "end_date":    end_date,
        "dates":       f"{start_date} to {end_date}",
    }
    for k, v in params.items():
        tool_context.state[k] = v

    tool_context.state["trip_params_summary"] = (
        f"Trip saved: {origin} → {destination}, {start_date} to {end_date}."
    )
    tool_context.actions.escalate = True
    return {
        "status":  "success",
        "message": f"Saved trip: {origin} → {destination}, "
                   f"{start_date} to {end_date}.",
    }


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC TOOL INSTANCES — conditionally created
# ═══════════════════════════════════════════════════════════════════════

if is_gemini_model():
    from google.adk.tools import google_search

    search_tool           = google_search
    coordinates_tool      = FunctionTool(_get_coordinates_tool)
    weather_tool          = FunctionTool(_get_weather_tool)
    save_trip_params_tool = FunctionTool(_save_trip_params_tool)
else:
    # Local models never use these — agents get tools=[]
    # Kept as None so accidental imports fail loudly.
    search_tool           = None
    coordinates_tool      = None
    weather_tool          = None
    save_trip_params_tool = None