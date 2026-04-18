from google.adk.agents import LlmAgent
from google.adk.tools import google_search

hotel_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="HotelAgent",
    description="Finds hotels near the planned activities in the destination.",
    instruction="""
        You are a hotel search specialist.

        Destination:        {destination}
        Travel dates:       {dates}
        Planned activities: {activities_info}

        Identify the neighbourhoods where the planned activities
        are concentrated.
        Use google_search to find well-rated hotels in or near
        those neighbourhoods in {destination}.

        For each hotel include:
        - Name
        - Neighbourhood / area
        - Approximate price per night
        - Which planned activities it is closest to

        Return ONLY hotel recommendations.
    """,
    tools=[google_search],
    output_key="hotel_info",
)