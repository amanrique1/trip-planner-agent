from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from agents.intake_agent import intake_agent
from agents.weather_agent import weather_agent
from agents.flight_agent import flight_agent
from agents.activities_agent import activities_agent
from agents.hotel_agent import hotel_agent


class TripPlannerAgent:
    _instance = None
    APP_NAME = "trip_planner"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TripPlannerAgent, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        if hasattr(self, "trip_coordinator"):
            return

        self.parallel_fetch = ParallelAgent(
            name="WeatherAndFlights",
            description="Fetch weather and flights simultaneously.",
            sub_agents=[weather_agent, flight_agent],
        )

        self.summary_agent = LlmAgent(
            model=model_name,
            name="SummaryAgent",
            description="Compiles the full trip itinerary from all previous outputs.",
            instruction="""
                You are a travel-planning editor.

                Trip: {origin} → {destination}
                Dates: {dates}

                Compile a polished, well-structured trip plan in Markdown
                from the following sections:

                ## Weather
                {weather_info}

                ## Flights
                {flight_info}

                ## Activities
                {activities_info}

                ## Hotels
                {hotel_info}

                Structure the output with:
                - A short introduction summarising the trip
                - Each section with clear headers
                - A day-by-day itinerary table combining weather,
                  activities, and hotel
                - A "Packing Tips" section based on the weather forecast
                - Use bullet points and tables where appropriate
            """,
            output_key="final_itinerary",
        )

        self.trip_coordinator = SequentialAgent(
            name="TripPlanner",
            description="End-to-end trip planner.",
            sub_agents=[
                intake_agent,
                self.parallel_fetch,
                activities_agent,
                hotel_agent,
                self.summary_agent,
            ],
        )

        self.session_service = InMemorySessionService()

        self.runner = Runner(
            agent=self.trip_coordinator,
            app_name=self.APP_NAME,
            session_service=self.session_service,
        )

    async def create_session(self, user_id: str) -> str:
        """Create a session and return its ID."""
        session = await self.session_service.create_session(
            app_name=self.APP_NAME,
            user_id=user_id,
        )
        return session.id

    async def run(self, user_id: str, session_id: str, message: str):
        user_content = Content(
            role="user",
            parts=[Part(text=message)],
        )
        return self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content,
        )