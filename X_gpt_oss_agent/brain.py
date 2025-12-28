import asyncio
import requests
import json
from tools import *

async def brain():
    await open_browser()

    # await open_url("https://x.com/home")
    await open_url("https://google.com")
    # await asyncio.sleep(3)

    action_history = ["no actions yet"]

    PROMPT = """post 'What an amazing year it was for software developers. Huge thanks to @Apple, @OpenAI, @Google, @Anthropic, @China and all other AI labs for making it fun."""
    reply_1 = """reply 'That said, I genuinely believe that these AI labs have hidden potential which they are not showing just to keep the US economy ahead of China, because the US economy is just staying ahead of China because of the top 10 software businesses."""
    reply_2 = """reply 'With today's AI labs potential, which I truly believe is more than they have shown, can automate all of the top 10 software companies businesses, infact all the pre-AI(old) software. If they have shown this year, China would have already been ahead of US in economy."""
    reply_3 = """reply 'I don't know what the take is here, but definitely it's not good for software developers who can build more and create more economy than pre-AI (old) software did."""
    reply_4 = """reply 'Only thing these models can't do is create more intelligent models than themselves (YET, who knows, maybe) or create business so that the US economy stays ahead of China."""
    reply_5 = """reply 'And by the way, this entire thread is being created using @gpt_oss20b model inferenced on MacBook M4 Pro 48GB Unified chip using browser agent. Zero API used."""
    reply_6 = """reply 'Next year is amazing in both software development with models(agents which can take down pre-AI software for good) and continued model intelligence specific to increase business. Can't wait to make models do all the pre-AI (old) software development automation!"""
    prompt_list = [PROMPT,reply_1,reply_2,reply_3,reply_4,reply_5,reply_6]
    i = 0
    while True:

        page_state = await get_page_state()

        if open("developer_window.txt", "r").read().strip():
            model_input = f"CURRENT PAGE STATE: {page_state} GOAL: {open("developer_window.txt", "r").read().strip()}"
            open("developer_window.txt", "w").write("")
        else:
            model_input = f"what would you click if the GOAL: {prompt_list[i]} previously you: {'\n'.join(action_history[-8:]) if action_history else '(no actions yet)'} CURRENT PAGE STATE: {page_state} \n What is the next tool call? Use the [index] numbers from the output below."

        model_output = requests.post("http://localhost:11434/api/chat",json={"model": "gpt-oss:20b","messages": [{"role": "system", "content": SYSTEM_PROMPT},{"role": "user", "content": model_input}],"tools": BROWSER_TOOLS,"stream": False},timeout=120).json().get("message", {})
        if not model_output:
            print("no model output")
            continue

        if not model_output.get("tool_calls"):
            print("no tool calls")
            continue

        tool_name,tool_args = model_output["tool_calls"][0]["function"]["name"], model_output["tool_calls"][0]["function"].get("arguments", {})

        if isinstance(tool_args, str):
            tool_args = json.loads(tool_args) if tool_args else {}

        func = globals().get(tool_name)
        try:
            result = await func(**tool_args)
        except Exception as e:
            result = str(e)
        action_history.append(f"{tool_name} {tool_args} result -> {result}")

        if tool_name == "click" and tool_args.get("index") == 13 or tool_args.get("index") == 12:
            i += 1

if __name__ == "__main__":
    asyncio.run(brain())