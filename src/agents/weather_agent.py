from google.adk.agents import LlmAgent
from agents.tools import coordinates_tool, weather_tool

weather_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="WeatherAgent",
    description="Fetches current and 7-day weather for the destination.",
    instruction="""
        You are a weather specialist.
        1. Call get_coordinates with the destination city.
        2. Call get_weather with the returned lat/long.
        3. Summarise the current conditions and the 7-day forecast
           (temperature range, rain/snow likelihood, UV index if available).
        Return ONLY the weather summary — no flight or hotel info.
    """,
    tools=[coordinates_tool, weather_tool],
    output_key="weather_info",
)