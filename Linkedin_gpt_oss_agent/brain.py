import asyncio
import requests
import json
from tools import *

async def brain():
    await open_browser()
    # await open_url("https://www.linkedin.com/jobs/collections/easy-apply/?currentJobId=4328143686&discover=true")
    await open_url("https://www.linkedin.com")

    action_history = []

    
    while True:

        page_state = await get_page_state()

        if open("developer_window.txt", "r").read().strip():
            model_input = f"CURRENT PAGE STATE: {page_state} GOAL: {open("developer_window.txt", "r").read().strip()}"
            print("developer_window.txt: ", model_input)
            open("developer_window.txt", "w").write("")
        else:
            model_input = f"GOAL: {PROMPT} previously you: {'\n'.join(action_history[-8:]) if action_history else '(no actions yet)'} CURRENT PAGE STATE: {page_state} What is the next action? Use the [index] numbers from the output above."
            print("model_input: ", model_input)
        # print("================================================================================================================================================\n")

        model_output = requests.post("http://localhost:11434/api/chat",json={"model": "gpt-oss:120b-cloud","messages": [{"role": "system", "content": SYSTEM_PROMPT},{"role": "user", "content": model_input}],"tools": BROWSER_TOOLS,"stream": False},timeout=120).json().get("message", {})
        if not model_output:
            continue
        
        # print("thinking: ", model_output.get("thinking", ""))

        # print("================================================================================================================================================\n")

        if not model_output.get("tool_calls"):
            continue

        tool_name,tool_args = model_output["tool_calls"][0]["function"]["name"], model_output["tool_calls"][0]["function"].get("arguments", {})
        # print("tool_name,tool_args: ", tool_name,tool_args)
        # print("================================================================================================================================================\n")
        if isinstance(tool_args, str):
            tool_args = json.loads(tool_args) if tool_args else {}
        print(tool_name,tool_args)

        func = globals().get(tool_name)
        try:
            result = await func(**tool_args)
        except Exception as e:
            result = str(e)
        action_history.append(result)
        # action_history.pop(0)

if __name__ == "__main__":
    asyncio.run(brain())