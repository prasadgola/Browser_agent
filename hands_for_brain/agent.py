# agent.py
from google.adk.agents import Agent
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

root_agent = Agent(
    name="job_application_agent",
    model="gemini-2.0-flash-exp",
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