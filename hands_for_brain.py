"""
Each event loop: goal + current browser state + single state of last action → model → single tool action
"""

import asyncio
import requests
from tool_schemas_of_gpt_oss20b import BROWSER_TOOLS
from prompts import SYSTEM_PROMPT
from tools import (
    open_browser, open_url, click, js_click, type_text,
    scroll, get_page_state, press_key, hover, upload_file_auto, 
    go_back, handle_alert, find_elements_by_text, click_element_with_text
)

TOOL_MAP = {
    "click": click,
    "js_click": js_click,
    "type_text": type_text,
    "scroll": scroll,
    # "get_page_state": get_page_state,
    "press_key": press_key,
    "hover": hover,
    "upload_file_auto": upload_file_auto,
    "go_back": go_back,
    "handle_alert": handle_alert,
    "find_elements_by_text": find_elements_by_text,
    "click_element_with_text": click_element_with_text,
}


def call_model(goal: str, browser_state: str, state_last_actions: list) -> dict:
    
    # Format last 3 actions for context
    actions_text = "None (first step)"
    if state_last_actions:
        actions_text = "\n".join([f"{i+1}. {action}" for i, action in enumerate(state_last_actions[-3:])])
    
    prompt = f"""GOAL: {goal}

                    PREVIOUS ACTIONS (last 3):
                    {actions_text}

                    CURRENT BROWSER STATE:
                    {browser_state}

                    IMPORTANT: Check the current URL and page title to understand where you are.
                    - If URL shows /feed/ you are already logged in
                    - If goal step is already done, move to the NEXT step

                    Based on the current state, what is the next action to achieve the goal?
                """

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "gpt-oss:20b",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "tools": BROWSER_TOOLS,
            "stream": False
        },
        timeout=120
    )
    return response.json()

async def loop(goal: str, max_events: int = 100):
    """Main agent loop"""
    
    await open_browser()
    await open_url("https://google.com")


    state_last_actions = []
    different_lens = {}
    
    for event in range(1, max_events + 1):
        
        #  create text book for brain to read
        if different_lens:
            browser_state = await find_elements_by_text(different_lens["text"], different_lens["element_type"])
        else:
            browser_state = await get_page_state(include_text=False)

        # capture the non deterministic brain energy by giving it the books created and put it in nerves
        response = call_model(goal, browser_state, state_last_actions)

        # unpack and push that brain energy signal to multiple nerves to reach all the body parts
        msg = response.get("message", {})
        brain_energy_signal = msg.get("tool_calls")

        # just in case if brain was numb and overwhelmed by seeing the textbook, then just wake it up
        if not brain_energy_signal:
            content = msg.get("content", "")
            print(f"  Model said when no tool calls: {content}")
            # just in case actually brain was not dumb or overthinking, then it has passed it's exam
            if "complete" in content.lower() or "done" in content.lower():
                print("\n✓ Task appears complete!")
                break
            continue
            
        
        # just check why brain was thinking before the hand physically moves
        # thinking = msg.get("thinking", "")
        # print("thinking brain thought: ",thinking)
        
        # continue unpacking the brain energy signal to multiple nerves until you reach that one nerve that lifts the hand and turns the book to next page
        one_signal = brain_energy_signal[0]
        name = one_signal["function"]["name"]
        print("name: ",name)
        args = one_signal["function"].get("arguments", {})
        if isinstance(args, str):
            import json
            print("args is string")
            args = json.loads(args) if args else {}

        #checkpoint: check if the brain thought that it wants to read the same page with different lens again   
        if name == "find_elements_by_text":
            print(args.get("text"))
            different_lens = {"text": args.get("text"), "element_type": args.get("element_type")}
            continue
        else:
            different_lens = {}

        #checkpoint: check if the brain thought that it has reached the last page of the book
        if name == "task_complete" or name == "task_failed":
            print(f"\n✓ TASK COMPLETE: {args.get('message', '')}")
            print(f"\n✗ TASK FAILED: {args.get('reason', '')}")
            break
        
        # respective signal is reaching to the finger tip to lift the hand and turn the page
        move_hand = TOOL_MAP.get(name)
        
        # if one of the finger is missing
        if not move_hand:
            print(f"  Unknown tool: {name}")
            continue
        # left the page
        result = await move_hand(**args)



        action_entry = f"{name}({args}) → {result}"
        state_last_actions.append(action_entry)

        print(len(state_last_actions))









    # send signal back to the brain to make brain know that hand has moved
    
    




        # if name == "click" and "✗" in result:
        #     print(f"  → Click failed, auto-retrying with js_click...")
        #     retry_result = await js_click(args["element_index"])
        #     print(f"  → Retry result: {retry_result}")
        #     result = retry_result
        #     action_entry = f"click({args}) FAILED → js_click → {retry_result}"
        # else:
        #     action_entry = f"{name}({args}) → {result}"
        
        # Add to history and keep only last 3
        # state_last_actions.append(action_entry)
        # if len(state_last_actions) > 3:
        #     state_last_actions.pop(0)
        
    
    
    # else:
    #     print(f"\n⚠ Reached max events ({max_events})")
    
    # print("\n" + "="*60)





if __name__ == "__main__":
    goal = """
    apply for software jobs on linkedin with username junk mail
    """

    asyncio.run(loop(goal))