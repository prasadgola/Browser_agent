"""
Each brain loop: goal + current browser state + single state of last action → model → single tool action
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

async def brain():
    """Main agent loop"""
    
    # giving book to brain with first page opened
    await open_browser()
    await open_url("https://google.com")

    # this is not signal from hand, it's previous hand
# it should be previous hand and page
    signals_from_hand = ""
    signals_from_eyes = ""


# check if signal from eyes state changes after brain calling the hands
    
    
    while True:



        # add few more lines to the page
        prompt = f"GOAL: apply for software jobs on linkedin with username junk mail. PREVIOUS ACTIONS (last 3): {signals_from_hand} CURRENT BROWSER STATE: {signals_from_eyes} Based on the current state, what is the next action to achieve the goal?"







        # giving brain all signals from eyes and hands and capture nurons that hits the nerves which are non deterministic signals
        row_signals_from_brain = requests.post(
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




            
        
        # just to check why brain was thinking before the hand physically moves
        # thinking = row_signals_from_brain.get("thinking", "")
        # print("thinking brain thought: ",thinking)
        





        # continue unpacking the brain signals to multiple nerves until you reach that one signal that lifts the hand and turns the book to next page
        one_signal = brain_signals[0]
        organ = one_signal["function"]["name"]
        print(organ)
        organ_signals = one_signal["function"].get("arguments", {})

        # print("args: ",args)

        if isinstance(organ_signals, str):
            import json
            print("organ_signals is string")
            organ_signals = json.loads(organ_signals) if organ_signals else {}
            print("organ_signals: ",organ_signals)






        #brain wants to see the same page
        if organ == "get_page_state":
            signals_from_eyes = await get_page_state(**organ_signals)
            continue
        if organ == "find_elements_by_text":
            signals_from_eyes = await find_elements_by_text(**organ_signals)
            continue



        
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
        turn_the_page = await hands(**organ_signals)




        # if page did not turn, use another hand to turn the page
        if organ == "click" and "✗" in turn_the_page:
            # turn the page with another hand
            retry_turn_the_page = await js_click(organ_signals["element_index"])
            print("jsclick")
            hand_signals_for_brain_after_page_turned = f"click({organ_signals}) FAILED → js_click → {retry_turn_the_page}"
        else:
            hand_signals_for_brain_after_page_turned = f"{organ}({organ_signals}) → {turn_the_page}"

        # send signal back to the brain to make brain about the hand move
        signals_from_hand += hand_signals_for_brain_after_page_turned + "\n"




if __name__ == "__main__":
    asyncio.run(brain())