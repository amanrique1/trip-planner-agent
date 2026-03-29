from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

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

        self.initial_coordinator = ParallelAgent(
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
                Read the following session state keys and compile a polished,
                well-structured trip plan in Markdown:

                - "weather_info"      → Weather overview section
                - "flight_info"       → Flights section
                - "activities_info"   → Activities & sightseeing section
                - "hotel_info"        → Accommodation section

                Add a short introduction and a helpful "packing tips" section
                based on the weather. Use headers, bullet points, and tables
                where appropriate.
            """,
            output_key="final_itinerary",
        )

        self.trip_coordinator = SequentialAgent(
            name="TripPlanner",
            description="End-to-end trip planner.",
            sub_agents=[
                self.initial_coordinator,
                activities_agent,
                hotel_agent,
                self.summary_agent,
            ],
        )

        # Explicit session service so we can create sessions
        self.session_service = InMemorySessionService()

        # Use Runner (not InMemoryRunner) with our own session service
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