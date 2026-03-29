from google.adk.agents import LlmAgent
from google.adk.tools import google_search


activities_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="ActivitiesAgent",
    description="Suggests activities and sightseeing based on the weather.",
    instruction="""
        You are a sightseeing and activities planner.
        Read the weather summary from the session state key "weather_info".

        Based on the forecast:
        • If rainy/cold  → prioritise museums, indoor markets, covered attractions.
        • If warm/sunny  → prioritise parks, walking tours, outdoor landmarks.
        • If mixed       → suggest a balanced mix.

        Use google_search to find the top-rated options at the destination.
        For each suggestion include name, brief description, and why it fits the weather.
        Return ONLY the activities list.
    """,
    tools=[google_search],
    output_key="activities_info",
)