import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if "/L2_tool_integration/" in str(item.fspath):
            item.add_marker(pytest.mark.L2)
            item.add_marker(pytest.mark.asyncio)


# ── Reusable state blobs (deterministic, no LLM needed) ────────────────

SAMPLE_WEATHER_RAW = {
    "daily_max": [22, 23, 25, 21, 24, 26, 22],
    "daily_min": [15, 16, 17, 14, 15, 18, 14],
    "weather_codes": [0, 1, 2, 51, 3, 0, 61],
    "dates": [
        "2025-06-10", "2025-06-11", "2025-06-12", "2025-06-13",
        "2025-06-14", "2025-06-15", "2025-06-16",
    ],
}

SAMPLE_WEATHER_INFO = (
    "Paris — 7-day forecast: Mostly sunny, highs 22-26 °C, "
    "lows 13-16 °C. Light rain expected on day 4 (code 51) "
    "and day 7 (code 61). UV index moderate."
)

SAMPLE_ACTIVITIES_INFO = (
    "Day 1 (Jun 10, sunny):  Jardin des Tuileries — outdoor park walk.\n"
    "Day 2 (Jun 11, clear):  Montmartre walking tour — outdoor.\n"
    "Day 3 (Jun 12, clear):  Seine river cruise — outdoor.\n"
    "Day 4 (Jun 13, rain):   Louvre Museum — indoor, world-class art.\n"
    "Day 5 (Jun 14, clear):  Versailles day trip — outdoor.\n"
    "Day 6 (Jun 15, sunny):  Champs-Élysées & Arc de Triomphe — outdoor.\n"
    "Day 7 (Jun 16, rain):   Musée d'Orsay — indoor, Impressionist collection.\n"
)

SAMPLE_FLIGHT_INFO = (
    "1. Air France AF001 — JFK → CDG, direct, ~7h 30m, ~$650.\n"
    "2. Delta DL264 — JFK → CDG, direct, ~7h 45m, ~$720.\n"
    "3. United UA57 → Lufthansa LH1023 — EWR → FRA → CDG, 1 stop, ~11h, ~$580.\n"
)

SAMPLE_HOTEL_INFO = (
    "1. Hôtel Le Marais — Le Marais, ~$180/night, near Louvre & Musée d'Orsay.\n"
    "2. Montmartre Residence — Montmartre, ~$140/night, near walking tour.\n"
)


# ── Fixtures for initial state per agent ────────────────────────────────

@pytest.fixture
def base_trip_state() -> dict:
    return {
        "origin": "New York",
        "destination": "Paris",
        "start_date": "2025-06-10",
        "end_date": "2025-06-17",
        "dates": "2025-06-10 to 2025-06-17",
    }


@pytest.fixture
def weather_agent_state(base_trip_state) -> dict:
    """State available when WeatherAgent runs (after IntakeAgent)."""
    return base_trip_state


@pytest.fixture
def flight_agent_state(base_trip_state) -> dict:
    """State available when FlightAgent runs (after IntakeAgent)."""
    return base_trip_state


@pytest.fixture
def activities_agent_state(base_trip_state) -> dict:
    """State available when ActivitiesAgent runs (after weather + flights)."""
    return {
        **base_trip_state,
        "weather_info": SAMPLE_WEATHER_INFO,
        "weather_raw": SAMPLE_WEATHER_RAW,
    }


@pytest.fixture
def hotel_agent_state(base_trip_state) -> dict:
    """State available when HotelAgent runs (after activities)."""
    return {
        **base_trip_state,
        "weather_info": SAMPLE_WEATHER_INFO,
        "weather_raw": SAMPLE_WEATHER_RAW,
        "activities_info": SAMPLE_ACTIVITIES_INFO,
    }


@pytest.fixture
def sample_weather_info() -> str:
    return SAMPLE_WEATHER_INFO


@pytest.fixture
def sample_weather_raw() -> dict:
    return SAMPLE_WEATHER_RAW


@pytest.fixture
def sample_activities_info() -> str:
    return SAMPLE_ACTIVITIES_INFO