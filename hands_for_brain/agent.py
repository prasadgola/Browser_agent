from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .prompts import primary_agent_instructions
from .tools import (
    open_browser,
    close_browser,
    mouse_click,
    mouse_move,
    mouse_right_click, 
    keyboard_type,
    scroll,
    screen_display
)

local_model = LiteLlm(
    model="ollama_chat/deepseek-v3.1:671b-cloud"
)

root_agent = Agent(
    name="job_application_agent",
    model=local_model,
    instruction=primary_agent_instructions(),
    tools=[
        open_browser,
        close_browser,
        mouse_click,
        mouse_move,
        mouse_right_click,
        keyboard_type,
        scroll,
        screen_display
    ]
)