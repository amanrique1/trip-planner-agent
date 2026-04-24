from config import get_model, is_gemini_model
from google.adk.agents import LlmAgent
from agents.utils.instruction_loader import get_instruction

_AGENT_NAME = "HotelAgent"
instruction = get_instruction(_AGENT_NAME, is_gemini_model())

extra_params = {}

if is_gemini_model():
    from agents.utils.tools import search_tool
    extra_params["tools"] = [search_tool]
else:
    from agents.utils.callbacks import prefetch_hotels
    extra_params["tools"] = []
    extra_params["before_agent_callback"] = prefetch_hotels

hotel_agent = LlmAgent(
    model=get_model(),
    name=_AGENT_NAME,
    description="Finds hotels near the planned activities in the destination.",
    instruction=instruction,
    output_key="hotel_info",
    **extra_params
)