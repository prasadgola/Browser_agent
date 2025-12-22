import asyncio
import requests
import json
from tools import *

async def brain():
    await open_browser()
    # await open_url("https://www.linkedin.com/jobs/collections/easy-apply/?currentJobId=4328143686&discover=true")
    await open_url("https://www.linkedin.com")
    await asyncio.sleep(3)

    action_history = []

    
    while True:
        
        page_state = await get_page_state2()
        # print(page_state)

        # print("================================================================================================================================================\n")

        if open("developer_window.txt", "r").read().strip():
            model_input = open("developer_window.txt", "r").read().strip()
            print("developer_window.txt: ", model_input)
            open("developer_window.txt", "w").write("")
        else:
            model_input = f"GOAL: {PROMPT} PREVIOUS ACTIONS:{'\n'.join(action_history[-8:]) if action_history else '(no actions yet)'} CURRENT PAGE STATE: {page_state} What is the next action? Use the [index] numbers from the output above."

        model_output = requests.post("http://localhost:11434/api/chat",json={"model": "gpt-oss:120b-cloud","messages": [{"role": "system", "content": SYSTEM_PROMPT},{"role": "user", "content": model_input}],"tools": BROWSER_TOOLS,"stream": False},timeout=120).json().get("message", {}).get("tool_calls", [])
        
        if not model_output:
            continue
        
        tool_name,tool_args = model_output[0]["function"]["name"], model_output[0]["function"].get("arguments", {})
        
        if isinstance(tool_args, str):
            tool_args = json.loads(tool_args) if tool_args else {}
        print(tool_name,tool_args)
        # print("================================================================================================================================================\n")

        func = globals().get(tool_name)
        try:
            result = await func(**tool_args)
        except Exception as e:
            result = str(e)
        action_history.append(f"{tool_name}({tool_args}) → {result}")

if __name__ == "__main__":
    asyncio.run(brain())