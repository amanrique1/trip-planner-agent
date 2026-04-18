import requests
from google.adk.tools import FunctionTool, ToolContext


def save_trip_params(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    tool_context: ToolContext,
) -> dict:
    """
    Save the extracted trip parameters to session state.

    Args:
        origin: Departure city, e.g. 'New York'
        destination: Arrival city, e.g. 'Paris'
        start_date: Trip start date, e.g. '2025-06-10'
        end_date: Trip end date, e.g. '2025-06-17'

    Returns:
        Confirmation of saved parameters.
    """
    params = {
        "origin": origin,
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "dates": f"{start_date} to {end_date}",
    }

    for key, value in params.items():
        tool_context.state[key] = value

    return {"status": "saved", **params}


def get_coordinates(city: str) -> dict:
    """
    Look up latitude and longitude for a given city name.

    Args:
        city: Name of the city, e.g. 'San Francisco'

    Returns:
        dict with lat, long, and resolved name, or an error key.
    """
    clean_city = city.split(",")[0].strip()
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": clean_city, "count": 1}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if "results" in data and data["results"]:
        r = data["results"][0]
        return {
            "lat": r["latitude"],
            "long": r["longitude"],
            "name": r["name"],
        }

    return {"error": f"Could not find coordinates for '{city}'"}


def get_weather(lat: float, long: float, tool_context: ToolContext) -> dict:
    """
    Fetch a 7-day weather forecast for given coordinates.

    Args:
        lat: Latitude of the location.
        long: Longitude of the location.

    Returns:
        JSON weather response with daily highs, lows, and weather codes.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": long,
        "current_weather": True,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "timezone": "auto",
        "forecast_days": 7,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    tool_context.state["weather_raw"] = {
        "daily_max": data["daily"]["temperature_2m_max"],
        "daily_min": data["daily"]["temperature_2m_min"],
        "weather_codes": data["daily"]["weathercode"],
        "dates": data["daily"]["time"],
    }

    return data


save_trip_params_tool = FunctionTool(save_trip_params)
coordinates_tool = FunctionTool(get_coordinates)
weather_tool = FunctionTool(get_weather)