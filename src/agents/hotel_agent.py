from google.adk.agents import LlmAgent
from google.adk.tools import google_search

hotel_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="HotelAgent",
    description="Finds hotels near the planned activities.",
    instruction="""
        You are a hotel search specialist.
        Read the activities list from the session state key "activities_info".

        Identify the neighbourhoods / areas where the activities are concentrated.
        Use google_search to find well-rated hotels in or very near those areas.
        For each hotel include: name, neighbourhood, approximate price per night,
        and which activities it is closest to.
        Return ONLY the hotel recommendations.
    """,
    tools=[google_search],
    output_key="hotel_info",
)