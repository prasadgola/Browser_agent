"""
Stateless Browser Automation Agent
Each loop: goal + current browser state → model → single tool action
"""

import asyncio
import requests
from tool_schemas import BROWSER_TOOLS

# Import all tool functions
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
    "get_page_state": get_page_state,
    "press_key": press_key,
    "hover": hover,
    "upload_file_auto": upload_file_auto,
    "go_back": go_back,
    "handle_alert": handle_alert,
    "find_elements_by_text": find_elements_by_text,
    "click_element_with_text": click_element_with_text,
}

SYSTEM_PROMPT = """You are a browser automation agent. You start at Google.com.

CORE WORKFLOW:
1. get_page_state() → See what's on page
2. Find target by index [0], [1] or use find_elements_by_text("name")
3. Interact: click(index), type_text(index, "text"), press_key("enter")
4. Repeat

RULES:
- ONE tool call per response
- Always get_page_state() after navigation/clicks
- If click() fails → try js_click() with same index
- Scroll if element not visible

LINKEDIN TIPS:
- Hover over "Connect" to see dropdown
- Profiles: Click name links
- Search bar at top

WHATSAPP TIPS:
- Contacts are role='listitem'
- Message box is [contenteditable='true']
- Press Enter to send
- Click attachment icon (📎) to send files

NAVIGATION:
- Start at Google → search for website → click result
- Use go_back() to return

When done: task_complete("summary")
If stuck: task_failed("reason")
"""


def call_model(goal: str, browser_state: str, last_action: str, failures: list) -> dict:
    
    failure_context = ""
    if failures:
        failure_context = f"""
FAILED ATTEMPTS THIS TASK:
{chr(10).join(failures[-3:])}  # Last 3 failures

If click() failed → try js_click() with same index
If element not found → scroll or use find_elements_by_text()
"""
    
    prompt = f"""GOAL: {goal}

{failure_context}

PREVIOUS ACTION:
{last_action or "None (first step)"}

CURRENT BROWSER STATE:
{browser_state}

IMPORTANT: Check the current URL and page title to understand where you are.
- If URL shows /feed/ you are already logged in
- If goal step is already done, move to the NEXT step

Based on the current state, what is the next action to achieve the goal?"""

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


async def execute_tool(name: str, args: dict) -> str:
    """Execute a tool and return result"""
    func = TOOL_MAP.get(name)
    if func:
        return await func(**args)
    return f"✗ Unknown tool: {name}"

async def click_send_button() -> str:
    """Find and click Send button (works for WhatsApp, LinkedIn, etc.)"""
    global driver
    
    try:
        # Try common Send button patterns
        selectors = [
            "[aria-label*='Send']",
            "[aria-label*='send']", 
            "[data-icon='send']",
            "button[type='submit']",
            "[role='button'][aria-label*='Send']",
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed():
                        el.click()
                        time.sleep(0.5)
                        return f"✓ Clicked Send button ({selector})"
            except:
                continue
        
        return "✗ Send button not found"
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def run_agent(goal: str, max_steps: int = 100):
    """Main agent loop"""
    
    print(f"\n{'='*60}")
    print(f"GOAL: {goal}")
    print(f"{'='*60}\n")
    
    import re
    file_match = re.search(r'([\w\-\.]+\.(pdf|doc|docx|xlsx|png|jpg|jpeg|txt|csv))', goal.lower())
    target_filename = file_match.group(1) if file_match else None
    
    if target_filename:
        print(f"  📎 Detected file to upload: {target_filename}")
    
    print("[Step 0] Opening browser at Google...")
    result = await open_browser()
    print(f"  → {result}")
    
    if "Failed" in result:
        print("Failed to open browser. Exiting.")
        return
    
    result = await open_url("https://google.com")
    print(f"  → {result}")
    
    last_action = None
    failures = []
    file_uploaded = False
    file_sent = False
    
    for step in range(1, max_steps + 1):
        print(f"\n[Step {step}]")
        
        browser_state = await get_page_state(include_text=False)
        print(f"  State: {browser_state[:500]}...")
        
        # DETECT states
        attachment_menu_open = "Document" in browser_state and "Photos & videos" in browser_state
        
        # DETECT: File preview showing
        file_preview_showing = (
            file_uploaded and 
            not file_sent and
            "Type a message" in browser_state and
            "1 page" in browser_state
        )
        
        # ===== AUTO-CLICK SEND AFTER UPLOAD =====
        if file_preview_showing:
            print(f"  📎 File preview detected, clicking Send via JS...")
            
            from tools import driver
            
            try:
                result = driver.execute_script("""
                    var sendBtn = document.querySelector('[aria-label="Send"]');
                    if (sendBtn) {
                        sendBtn.click();
                        return 'clicked';
                    }
                    return 'not found';
                """)
                print(f"  JS result: {result}")
                
                if result == 'clicked':
                    file_sent = True
                    last_action = "✓ Clicked Send button"
                    await asyncio.sleep(1)
                    continue
            except Exception as e:
                print(f"  JS error: {e}")
        
        # Call model
        response = call_model(goal, browser_state, last_action, failures)
        msg = response.get("message", {})
        tool_calls = msg.get("tool_calls")
        
        if not tool_calls:
            content = msg.get("content", "")
            print(f"  Model said: {content}")
            if "complete" in content.lower() or "done" in content.lower():
                print("\n✓ Task appears complete!")
                break
            continue
        
        tc = tool_calls[0]
        name = tc["function"]["name"]
        args = tc["function"].get("arguments", {})
        
        if isinstance(args, str):
            import json
            args = json.loads(args) if args else {}
        
        # ===== INTERCEPT BAD ACTIONS =====
        
        if attachment_menu_open and target_filename and not file_uploaded:
            print(f"  ⚠️ INTERCEPTED: Menu open, forcing upload_file_auto")
            name = "upload_file_auto"
            args = {"file_path": target_filename}
        
        elif attachment_menu_open and file_uploaded:
            print(f"  ⚠️ INTERCEPTED: Menu open but already uploaded, pressing escape")
            name = "press_key"
            args = {"key": "escape"}
        
        print(f"  Action: {name}({args})")
        
        if name == "task_complete":
            print(f"\n✓ TASK COMPLETE: {args.get('message', '')}")
            break
        
        if name == "task_failed":
            print(f"\n✗ TASK FAILED: {args.get('reason', '')}")
            break
        
        # Execute the tool
        result = await execute_tool(name, args)
        print(f"  Result: {result}")
        
        if name == "upload_file_auto" and "✓" in result:
            file_uploaded = True
            print(f"  📎 File upload tracked - won't upload again")
        
        if "✗" in result:
            failures.append(f"{name}({args}) → {result}")
        
        if name == "click" and "✗" in result:
            print(f"  → Click failed, auto-retrying with js_click...")
            retry_result = await js_click(args["element_index"])
            print(f"  → Retry result: {retry_result}")
            result = retry_result
            last_action = f"click({args}) FAILED → js_click → {retry_result}"
        else:
            last_action = f"{name}({args}) → {result}"
        
        await asyncio.sleep(0.5)
    
    else:
        print(f"\n⚠ Reached max steps ({max_steps})")
    
    print("\n" + "="*60)


async def main():
    # Example usage
    # goal = input("Enter your goal (or press Enter for default): ").strip()
    goal = """
    apply for software jobs on indeed with username tobasavaprasad@gmail.com
    Use button like continue or apply.
    """
    
    if not goal:
        goal = "Go to google.com and search for 'weather today'"
    
    await run_agent(goal)


if __name__ == "__main__":
    asyncio.run(main())