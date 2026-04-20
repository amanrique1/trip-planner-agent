from config import get_model, is_gemini_model
from google.adk.agents import LlmAgent
from agents.utils.instruction_loader import get_instruction

_AGENT_NAME = "WeatherAgent"
instruction = get_instruction(_AGENT_NAME, is_gemini_model())

extra_params = {}

if is_gemini_model():
    from agents.tools import coordinates_tool, weather_tool
    extra_params["tools"] = [coordinates_tool, weather_tool]
else:
    from agents.utils.callbacks import prefetch_weather
    extra_params["tools"] = []
    extra_params["before_agent_callback"] = prefetch_weather

weather_agent = LlmAgent(
    model=get_model(),
    name=_AGENT_NAME,
    description="Fetches current and 7-day weather for the destination.",
    instruction=instruction,
    output_key="weather_info",
    **extra_params
)