"""
Each brain loop: goal + current browser state + single state of last action → model → single tool action
"""

import asyncio
import requests
from prompts_gpt_oss20b import BROWSER_TOOLS, SYSTEM_PROMPT, PROMPT
from tools import (
    open_browser, open_url, click, js_click, type_text,
    scroll, get_page_state, press_key, hover, upload_file_auto, 
    go_back, handle_alert, find_elements_by_text, click_element_with_text
)

async def brain():
    """Main agent loop"""
    
    # giving book to brain with first page opened
    await open_browser()
    await open_url("https://google.com")

    signals_from_hand = []
    signals_from_eyes = await get_page_state() 
    state_of_failure_prompt = ""
    failure_count = 0

    while True:

        # add few more lines to the page
        STATE_FULL_PROMPT = f"GOAL: {PROMPT} \n PREVIOUS ACTIONS: {"\n".join([f"{i+1}. {action}" for i, action in enumerate(signals_from_hand)])} CURRENT BROWSER STATE: {signals_from_eyes} {state_of_failure_prompt} Based on the current state, what is the next action to achieve the goal?"

        # giving brain all signals from eyes and hands and capture nurons that hits the nerves which are non deterministic signals
        row_signals_from_brain = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "gpt-oss:20b",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": STATE_FULL_PROMPT}
                ],
                "tools": BROWSER_TOOLS,
                "stream": False
            },
            timeout=120
        ).json()

        # unpack the brain signals to send to multiple nerves that reach different organs
        less_row_brain_signals = row_signals_from_brain.get("message", {})
        brain_signals = less_row_brain_signals.get("tool_calls")

        # if brain was numb and did not give any signals to organs
        if not brain_signals:
            content = less_row_brain_signals.get("content", "")
            print(f"Brain said when no signals: {content}")
            # if brain was not numb but says it has completed the task
            if "complete" in content.lower() or "done" in content.lower():
                print("\n✓ Task appears complete!")
                break
            continue

        # continue unpacking the brain signals to multiple nerves until you reach that one signal that lifts the hand and turns the book to next page
        one_signal = brain_signals[0]
        organ = one_signal["function"]["name"]
        organ_signals = one_signal["function"].get("arguments", {})

        if isinstance(organ_signals, str):
            import json
            print("organ_signals is string")
            organ_signals = json.loads(organ_signals) if organ_signals else {}
            print("organ_signals: ",organ_signals)

        #brain wants to see the same page
        if organ == "find_elements_by_text":
            signals_from_eyes = await find_elements_by_text(**organ_signals)
            continue
        elif organ == "get_page_state":
            signals_from_eyes = await get_page_state(**organ_signals)
            continue
        else:
            signals_from_eyes = await get_page_state()

        #checkpoint: check if the brain thought that it has reached the last page of the book
        if organ == "task_complete" or organ == "task_failed":
            print(f"\n✓ TASK COMPLETE: {organ_signals.get('message', '')}")
            print(f"\n✗ TASK FAILED: {organ_signals.get('reason', '')}")
            break
        
        #signal should reach to the hand to lift the hand and turn the page
        hands = globals().get(organ)
        
        # if hand is missing
        if not hands:
            print(f"  Unknown hand: {organ}")
            continue

        # turn the page ******
        try:
            turn_the_page = await hands(**organ_signals)
        except Exception as e:
            turn_the_page = f"✗ Error executing {organ}: {str(e)}"
            print(f"⚠️ Tool execution error: {e}")

        # if page did not turn, use another hand to turn the page
        if organ == "click" and "✗" in turn_the_page:
            # turn the page with another hand
            retry_turn_the_page = await js_click(organ_signals["element_index"])
            # print("jsclick")
            hand_signals_for_brain_after_page_turned = f"click({organ_signals}) FAILED → js_click → {retry_turn_the_page}"
        else:
            hand_signals_for_brain_after_page_turned = f"{organ}({organ_signals}) → {turn_the_page}"

        if "✗" in turn_the_page:
            failure_count += 1
            if failure_count > 1:
                state_of_failure_prompt += f"\nPREVIOUS ACTION FAILED {failure_count} TIMES. Try alternative approach or use task_failed."
        else:
            failure_count = 0
            state_of_failure_prompt = ""

        # send signal back to the brain to make brain about the hand move
        signals_from_hand.append(hand_signals_for_brain_after_page_turned)
        if len(signals_from_hand) > 10:
            signals_from_hand = signals_from_hand[-10:]

if __name__ == "__main__":
    asyncio.run(brain())