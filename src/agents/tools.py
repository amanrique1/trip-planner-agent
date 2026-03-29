import requests
from google.adk.tools import FunctionTool


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
        return {"lat": r["latitude"], "long": r["longitude"], "name": r["name"]}
    return {"error": f"Could not find coordinates for '{city}'"}


def get_weather(lat: float, long: float) -> dict:
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
    return response.json()


coordinates_tool = FunctionTool(get_coordinates)
weather_tool = FunctionTool(get_weather)