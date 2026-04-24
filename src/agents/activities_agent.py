from config import get_model, is_gemini_model
from google.adk.agents import LlmAgent
from agents.utils.instruction_loader import get_instruction

_AGENT_NAME = "ActivitiesAgent"
instruction = get_instruction(_AGENT_NAME, is_gemini_model())

extra_params = {}

if is_gemini_model():
    from agents.utils.tools import search_tool
    extra_params["tools"] = [search_tool]
else:
    from agents.utils.callbacks import prefetch_activities
    extra_params["tools"] = []
    extra_params["before_agent_callback"] = prefetch_activities

activities_agent = LlmAgent(
    model=get_model(),
    name=_AGENT_NAME,
    description="Plans daily activities based on destination and weather.",
    instruction=instruction,
    output_key="activities_info",
    **extra_params
)