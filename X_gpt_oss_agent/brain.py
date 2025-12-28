import asyncio
import requests
import json
from tools import *

async def brain():
    await open_browser()

    await open_url("https://x.com/home")
    # await open_url("https://google.com")
    # await asyncio.sleep(3)

    action_history = []

    
    while True:

        page_state = await get_page_state()
        print(page_state)
        print("====================================================================================================================================================================================================")

        if open("developer_window.txt", "r").read().strip():
            model_input = f"CURRENT PAGE STATE: {page_state} GOAL: {open("developer_window.txt", "r").read().strip()}"
            open("developer_window.txt", "w").write("")
        else:
            model_input = f"what would you click if the GOAL: {PROMPT} previously you: {'\n'.join(action_history[-8:]) if action_history else '(no actions yet)'} CURRENT PAGE STATE: {page_state} \n What is the next tool call? Use the [index] numbers from the output below."

        model_output = requests.post("http://localhost:11434/api/chat",json={"model": "gpt-oss:20b","messages": [{"role": "system", "content": SYSTEM_PROMPT},{"role": "user", "content": model_input}],"tools": BROWSER_TOOLS,"stream": False},timeout=120).json().get("message", {})
        if not model_output:
            print("no model output")
            continue

        if not model_output.get("tool_calls"):
            print("no tool calls")
            continue

        tool_name,tool_args = model_output["tool_calls"][0]["function"]["name"], model_output["tool_calls"][0]["function"].get("arguments", {})
        print(tool_name,tool_args)
        print("====================================================================================================================================================================================================")

        if isinstance(tool_args, str):
            tool_args = json.loads(tool_args) if tool_args else {}

        func = globals().get(tool_name)
        try:
            result = await func(**tool_args)
        except Exception as e:
            result = str(e)
        action_history.append(f"{tool_name} {tool_args} result -> {result}")
        # action_history.pop(0)

if __name__ == "__main__":
    asyncio.run(brain())