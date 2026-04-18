from google.adk.agents import LlmAgent
from google.adk.tools import google_search

activities_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="ActivitiesAgent",
    description="Plans daily activities based on destination and weather.",
    instruction="""
        You are an activities planner.

        Destination:      {destination}
        Travel dates:     {dates}
        Weather forecast: {weather_raw}
        Weather summary:  {weather_info}

        Use the weather codes to decide indoor vs outdoor each day:
          - Codes 0-3:   clear / partly cloudy → prefer outdoor activities
          - Codes 45-48: fog → outdoor OK but suggest visibility-friendly options
          - Codes 51-67: rain → suggest indoor alternatives
          - Codes 71-77: snow → suggest indoor alternatives

        Use google_search to find popular attractions, tours, and
        restaurants in {destination}.

        Group activities by day, matching the forecast dates.
        For each activity include: name, brief description, and
        whether it is indoor or outdoor.
        Return ONLY the activities list.
    """,
    tools=[google_search],
    output_key="activities_info",
)