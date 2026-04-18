from google.adk.agents import LlmAgent
from google.adk.tools import google_search

flight_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="FlightAgent",
    description="Searches for flight options between origin and destination.",
    instruction="""
        You are a flight search specialist.

        Origin:      {origin}
        Destination: {destination}
        Dates:       {dates}

        Use google_search to find the best flight options
        (direct and connecting) for these dates.
        For each option include: airline, route, approximate price,
        and total travel duration.
        Return ONLY flight information.
    """,
    tools=[google_search],
    output_key="flight_info",
)