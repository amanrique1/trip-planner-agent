from google.adk.agents import LlmAgent
from agents.tools import save_trip_params_tool

intake_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="IntakeAgent",
    description="Extracts trip parameters from the user message and saves them to state.",
    instruction="""
        You are a trip parameter extractor.

        From the user's message, identify:
        - origin: the departure city
        - destination: the arrival city
        - start_date: in YYYY-MM-DD format
        - end_date: in YYYY-MM-DD format

        If the user gives relative dates like "next week", estimate
        based on today's date.
        If any parameter is unclear or missing, pick a reasonable
        default and note your assumption.

        You MUST call save_trip_params exactly once with all four values.
        After the tool call succeeds, reply with a short confirmation
        of the trip details you understood.
    """,
    tools=[save_trip_params_tool],
    output_key="trip_params_summary",
)