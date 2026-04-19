from config import get_model

from google.adk.agents import LlmAgent
from agents.tools import coordinates_tool, weather_tool

weather_agent = LlmAgent(
    model=get_model(),
    name="WeatherAgent",
    description="Fetches current and 7-day weather for the destination.",
    instruction="""
        You are a weather specialist.
        The destination city is: {destination}
        Travel dates: {dates}

        Steps:
        1. Call get_coordinates with the destination city.
        2. Call get_weather with the returned lat and long.
        3. Summarise the current conditions and the 7-day forecast
           covering: daily high/low temperatures, rain or snow
           likelihood based on weather codes, and general trends.

        Return ONLY the weather summary — no flight or hotel info.
    """,
    tools=[coordinates_tool, weather_tool],
    output_key="weather_info",
)