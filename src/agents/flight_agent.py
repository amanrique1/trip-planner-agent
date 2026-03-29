from google.adk.agents import LlmAgent
from google.adk.tools import google_search

flight_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="FlightAgent",
    description="Searches for flight options between origin and destination.",
    instruction="""
        You are a flight search specialist.
        Use google_search to find the best flight options
        (direct & connecting) from the origin city to the destination city.
        Include airlines, approximate prices, and duration.
        Return ONLY flight information.
    """,
    tools=[google_search],
    output_key="flight_info",
)