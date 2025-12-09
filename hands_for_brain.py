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


async def whatsapp_upload_document(driver, file_path: str) -> str:
    """
    WhatsApp-specific upload that:
    1. Clicks "Document" button in attachment menu
    2. Waits for file input to be ready
    3. Sends file to the correct input
    """
    import os
    from selenium.webdriver.common.by import By
    
    print("  📎 WhatsApp upload flow started...")
    
    # Resolve file path
    file_path = os.path.expanduser(file_path)
    
    if not os.path.isabs(file_path):
        for base in [os.getcwd(), os.path.expanduser('~/Documents'), 
                     os.path.expanduser('~/Downloads'), os.path.expanduser('~/Desktop')]:
            full = os.path.join(base, file_path)
            if os.path.exists(full):
                file_path = full
                break
    
    if not os.path.exists(file_path):
        return f"✗ File not found: {file_path}"
    
    try:
        # Step 1: Click "Document" button
        print("  Step 1: Looking for Document button...")
        
        doc_clicked = driver.execute_script("""
            // Try multiple selectors for Document button
            var selectors = [
                '[data-icon="attach-document"]',
                'span[data-icon="attach-document"]',
                'li[data-animate-dropdown-item="2"]',  // Document is usually 2nd item
                'button[aria-label*="Document"]'
            ];
            
            for (var i = 0; i < selectors.length; i++) {
                var el = document.querySelector(selectors[i]);
                if (el) {
                    // Find clickable parent if needed
                    var clickTarget = el.closest('button') || el.closest('li') || el.closest('[role="button"]') || el;
                    clickTarget.click();
                    return 'clicked: ' + selectors[i];
                }
            }
            
            // Fallback: find by text content
            var items = document.querySelectorAll('li, div[role="button"], button');
            for (var j = 0; j < items.length; j++) {
                if (items[j].textContent.includes('Document')) {
                    items[j].click();
                    return 'clicked by text';
                }
            }
            
            return 'not found';
        """)
        
        print(f"  Document button: {doc_clicked}")
        
        if doc_clicked == 'not found':
            return "✗ Could not find Document button in menu"
        
        # Step 2: Wait for file input to be ready
        await asyncio.sleep(1)
        
        # Step 3: Find and use the correct file input
        print("  Step 2: Finding file input...")
        
        # Get all file inputs
        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        print(f"  Found {len(file_inputs)} file inputs")
        
        # Log them
        for i, fi in enumerate(file_inputs):
            accept = fi.get_attribute("accept") or "(none)"
            print(f"    [{i}] accept='{accept}'")
        
        # For documents, we want the input that:
        # - Has accept="*" OR
        # - Has no accept attribute OR  
        # - Doesn't have "image" in accept
        
        target_input = None
        for fi in file_inputs:
            accept = (fi.get_attribute("accept") or "").lower()
            if accept == "*" or accept == "" or "image" not in accept:
                target_input = fi
                print(f"  Selected input with accept='{accept}'")
                break
        
        # Fallback to last input
        if not target_input and file_inputs:
            target_input = file_inputs[-1]
            print("  Using last input as fallback")
        
        if not target_input:
            return "✗ No file input found after clicking Document"
        
        # Step 4: Send file
        print(f"  Step 3: Sending file {os.path.basename(file_path)}...")
        target_input.send_keys(file_path)
        
        await asyncio.sleep(2)  # Wait for preview
        
        return f"✓ Document uploaded: {os.path.basename(file_path)}"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"✗ Upload failed: {str(e)}"


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
    
    # Import driver for direct access
    from tools import driver
    
    for step in range(1, max_steps + 1):
        print(f"\n[Step {step}]")
        
        browser_state = await get_page_state(include_text=False)
        print(f"  State: {browser_state[:500]}...")
        
        # Detect WhatsApp
        is_whatsapp = 'whatsapp' in browser_state.lower() or 'whatsapp' in driver.current_url.lower()
        
        # DETECT: Attachment menu is open (has Document option visible)
        attachment_menu_open = "Document" in browser_state and "Photos" in browser_state
        
        # DETECT: File preview showing (ready to send)
        file_preview_showing = (
            file_uploaded and 
            not file_sent and
            ("Type a message" in browser_state or "Add a caption" in browser_state or "1 page" in browser_state)
        )
        
        # ===== WHATSAPP: AUTO-HANDLE ATTACHMENT MENU =====
        if is_whatsapp and attachment_menu_open and target_filename and not file_uploaded:
            print(f"  📎 WHATSAPP: Attachment menu detected, using special upload flow...")
            
            result = await whatsapp_upload_document(driver, target_filename)
            print(f"  Result: {result}")
            
            if "✓" in result:
                file_uploaded = True
                last_action = result
            else:
                failures.append(result)
                last_action = result
            
            await asyncio.sleep(1)
            continue
        
        # ===== AUTO-CLICK SEND AFTER UPLOAD =====
        if file_preview_showing:
            print(f"  📎 File preview detected, clicking Send...")
            
            try:
                result = driver.execute_script("""
                    // Try multiple Send button selectors
                    var selectors = [
                        '[aria-label="Send"]',
                        '[data-icon="send"]',
                        'span[data-icon="send"]',
                        'button[aria-label*="Send"]'
                    ];
                    
                    for (var i = 0; i < selectors.length; i++) {
                        var el = document.querySelector(selectors[i]);
                        if (el) {
                            var btn = el.closest('button') || el.closest('[role="button"]') || el;
                            btn.click();
                            return 'clicked: ' + selectors[i];
                        }
                    }
                    return 'not found';
                """)
                print(f"  Send button: {result}")
                
                if result != 'not found':
                    file_sent = True
                    last_action = "✓ Clicked Send button"
                    await asyncio.sleep(1)
                    continue
            except Exception as e:
                print(f"  Send error: {e}")
        
        # ===== NORMAL MODEL FLOW =====
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
        
        # ===== INTERCEPT: If model tries to upload on WhatsApp, use special flow =====
        if is_whatsapp and name == "upload_file_auto" and not file_uploaded:
            print(f"  ⚠️ Redirecting to WhatsApp upload flow...")
            result = await whatsapp_upload_document(driver, args.get("file_path", target_filename))
            print(f"  Result: {result}")
            
            if "✓" in result:
                file_uploaded = True
            else:
                failures.append(result)
            
            last_action = result
            await asyncio.sleep(0.5)
            continue
        
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
            print(f"  📎 File upload tracked")
        
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
    goal = """
    send basavaprasad_resume.pdf to channu on whatsapp.
    """
    
    if not goal:
        goal = "Go to google.com and search for 'weather today'"
    
    await run_agent(goal)


if __name__ == "__main__":
    asyncio.run(main())