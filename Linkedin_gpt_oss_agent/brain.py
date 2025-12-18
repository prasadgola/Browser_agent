import asyncio
import requests
import json
from tools import *

async def brain():
    await open_browser()
    await open_url("https://www.linkedin.com/jobs/")

    action_history = []

    
    while True:
        

        page_state = await get_page_state()
        print(page_state)  
        
        user_prompt = f"""GOAL: {PROMPT} PREVIOUS ACTIONS:{"\n".join(action_history[-8:]) if action_history else "(no actions yet)"} CURRENT PAGE STATE: {page_state} What is the next action? Use the [index] numbers from the output above."""

        model_output = requests.post("http://localhost:11434/api/chat",json={"model": "gpt-oss:20b","messages": [{"role": "system", "content": SYSTEM_PROMPT},{"role": "user", "content": user_prompt}],"tools": BROWSER_TOOLS,"stream": False},timeout=120).json().get("message", {}).get("tool_calls", [])
        
        if not model_output:
            continue
        
        tool_name,tool_args = model_output[0]["function"]["name"], model_output[0]["function"].get("arguments", {})
        print(tool_name,tool_args)
        
        if isinstance(tool_args, str):
            tool_args = json.loads(tool_args) if tool_args else {}

        func = globals().get(tool_name)
        try:
            result = await func(**tool_args)
        except Exception as e:
            result = str(e)
        action_history.append(f"{tool_name}({tool_args}) → {result}")


if __name__ == "__main__":
    asyncio.run(brain())