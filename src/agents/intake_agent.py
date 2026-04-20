from config import get_model, is_gemini_model
from google.adk.agents import LlmAgent
from agents.utils.instruction_loader import get_instruction

_AGENT_NAME = "IntakeAgent"
instruction = get_instruction(_AGENT_NAME, is_gemini_model())

extra_params = {}

if is_gemini_model():
    from agents.tools import save_trip_params_tool
    extra_params["tools"] = [save_trip_params_tool]
else:
    from agents.utils.callbacks import store_trip_params
    extra_params["tools"] = []
    extra_params["output_key"] = "trip_params_raw"
    extra_params["after_agent_callback"] = store_trip_params

intake_agent = LlmAgent(
    model=get_model(),
    name=_AGENT_NAME,
    description="Extracts trip parameters from the user message.",
    instruction=instruction,
    **extra_params
)