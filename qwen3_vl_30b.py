import os
import requests
import base64
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import cv2
import numpy as np
from PIL import Image
import io

# Screenshot display settings
SHOW_SCREENSHOTS = True  # Set to False to disable
SCREENSHOT_WINDOW_NAME = "Browser Agent View"
SCREENSHOT_SAVE_DIR = os.path.expanduser("~/AI Studio/screenshots")  # Optional: save screenshots

driver = None

def open_browser():
    global driver
    options = uc.ChromeOptions()
    options.add_argument('--start-maximized')
    profile_path = os.path.expanduser('~/AI Studio/chrome_automation_profile')
    options.add_argument(f'--user-data-dir={profile_path}')
    driver = uc.Chrome(options=options)
    print(f"Browser opened with profile: {profile_path}")

def open_url(url):
    global driver
    driver.get(url)
    time.sleep(2)
    print(f"Navigated to {url}")

# === COORDINATE SCALING ===
def get_viewport_size():
    """Get the actual viewport size"""
    global driver
    return driver.execute_script("return {width: window.innerWidth, height: window.innerHeight}")

def scale_coordinates(x, y):
    """
    Scale coordinates from the fixed screenshot size to actual viewport size.
    Model sees SCREENSHOT_WIDTH x SCREENSHOT_HEIGHT image.
    We need to map those coordinates to the actual viewport.
    """
    global driver
    
    # Get viewport size
    viewport = get_viewport_size()
    viewport_w, viewport_h = viewport['width'], viewport['height']
    
    # Calculate scale factors from screenshot size to viewport
    scale_x = viewport_w / SCREENSHOT_WIDTH
    scale_y = viewport_h / SCREENSHOT_HEIGHT
    
    # Scale the coordinates
    scaled_x = int(x * scale_x)
    scaled_y = int(y * scale_y)
    
    print(f"  Screenshot sent: {SCREENSHOT_WIDTH}x{SCREENSHOT_HEIGHT}")
    print(f"  Viewport size: {viewport_w}x{viewport_h}")
    print(f"  Scale factors: x={scale_x:.3f}, y={scale_y:.3f}")
    print(f"  Original: ({x}, {y}) -> Scaled: ({scaled_x}, {scaled_y})")
    
    return scaled_x, scaled_y

# === HELPER FUNCTION ===
def parse_coordinates(x, y=None):
    """Parse coordinates - handles both [x1, x2] format and (x, y) format"""
    if isinstance(x, list) and len(x) == 2:
        return (x[0] + x[1]) // 2
    return x

def get_click_point(x, y):
    """Convert bounding box to center point - NO scaling needed"""
    center_x = parse_coordinates(x)
    center_y = parse_coordinates(y)
    return center_x, center_y 

# === VISUAL INDICATOR ===
def show_click_indicator(x, y, color="red"):
    global driver
    driver.execute_script(f"""
        document.querySelectorAll('.click-indicator').forEach(el => el.remove());
        
        var ring = document.createElement('div');
        ring.className = 'click-indicator';
        ring.style.cssText = `
            position: fixed;
            left: {x - 20}px;
            top: {y - 20}px;
            width: 40px;
            height: 40px;
            border: 3px solid {color};
            border-radius: 50%;
            pointer-events: none;
            z-index: 999999;
            animation: clickPulse 0.6s ease-out forwards;
        `;
        
        var dot = document.createElement('div');
        dot.className = 'click-indicator';
        dot.style.cssText = `
            position: fixed;
            left: {x - 6}px;
            top: {y - 6}px;
            width: 12px;
            height: 12px;
            background: {color};
            border-radius: 50%;
            pointer-events: none;
            z-index: 999999;
            box-shadow: 0 0 10px {color};
        `;
        
        if (!document.getElementById('click-indicator-style')) {{
            var style = document.createElement('style');
            style.id = 'click-indicator-style';
            style.textContent = `
                @keyframes clickPulse {{
                    0% {{ transform: scale(0.5); opacity: 1; }}
                    50% {{ transform: scale(1.2); opacity: 0.8; }}
                    100% {{ transform: scale(1.5); opacity: 0; }}
                }}
            `;
            document.head.appendChild(style);
        }}
        
        document.body.appendChild(ring);
        document.body.appendChild(dot);
        
        setTimeout(() => {{
            ring.remove();
            dot.remove();
        }}, 1500);
    """)

def mouse_click(x, y=None):
    """Click at specific coordinates"""
    global driver
    print('hello from mouse_click')
    
    # Handle missing y parameter
    if y is None:
        print(f"ERROR: Missing y coordinate. Received x={x}, y={y}")
        return "Failed to click: Both x and y coordinates are required"
    
    try:
        # Get center point from bounding box
        center_x = parse_coordinates(x)
        center_y = parse_coordinates(y)
        
        print(f"Target point: ({center_x}, {center_y})")
        
        # Show visual indicator
        show_click_indicator(center_x, center_y, "red")
        print('hello from inside mouse_click')
        time.sleep(0.8)
        
        # Click directly at coordinates
        print(f"Clicking at ({center_x}, {center_y})")
        driver.execute_script(f"""
            var element = document.elementFromPoint({center_x}, {center_y});
            if (element) {{
                element.click();
                console.log('Clicked element:', element);
            }} else {{
                console.log('No element found at coordinates');
            }}
        """)
        
        time.sleep(0.5)
        return f"Clicked at ({center_x}, {center_y})"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Failed to click: {str(e)}"

# Add alias for backward compatibility
def click(x, y=None):
    """Alias for mouse_click"""
    return mouse_click(x, y)

def type_text(text):
    """Type text at current focus"""
    global driver
    try:
        # Find the active element and type
        active_element = driver.switch_to.active_element
        active_element.send_keys(text)
        time.sleep(0.5)
        return f"Typed: {text}"
    except Exception as e:
        return f"Failed to type: {str(e)}"

def press_key(key):
    """Press a keyboard key (Enter, Tab, Escape, Backspace, etc)"""
    global driver
    try:
        active_element = driver.switch_to.active_element
        key_map = {
            "Enter": Keys.RETURN,
            "Tab": Keys.TAB,
            "Escape": Keys.ESCAPE,
            "Backspace": Keys.BACK_SPACE,
            "Delete": Keys.DELETE,
            "ArrowUp": Keys.ARROW_UP,
            "ArrowDown": Keys.ARROW_DOWN,
            "ArrowLeft": Keys.ARROW_LEFT,
            "ArrowRight": Keys.ARROW_RIGHT,
        }
        active_element.send_keys(key_map.get(key, key))
        time.sleep(0.5)
        return f"Pressed: {key}"
    except Exception as e:
        return f"Failed to press key: {str(e)}"

def scroll(direction, amount=300):
    """Scroll the page"""
    global driver
    try:
        if direction == "down":
            driver.execute_script(f"window.scrollBy(0, {amount});")
        elif direction == "up":
            driver.execute_script(f"window.scrollBy(0, -{amount});")
        time.sleep(0.5)
        return f"Scrolled {direction} by {amount}px"
    except Exception as e:
        return f"Failed to scroll: {str(e)}"


def take_screenshot(action_num=None, show=True):
    """Take screenshot at native resolution, optionally display, and return base64"""
    global driver
    screenshot_png = driver.get_screenshot_as_png()
    
    # Use native resolution - no resizing
    img = Image.open(io.BytesIO(screenshot_png))
    screenshot_b64 = base64.b64encode(screenshot_png).decode('utf-8')

    
    if SHOW_SCREENSHOTS and show:
        # Convert to numpy array for OpenCV display
        img_array = np.array(img)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Add action number overlay if provided
        if action_num is not None:
            cv2.putText(img_cv, f"Action {action_num}", (20, 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Resize for display only if too large
        h, w = img_cv.shape[:2]
        max_height = 900
        if h > max_height:
            scale = max_height / h
            display_img = cv2.resize(img_cv, (int(w * scale), int(h * scale)))
        else:
            display_img = img_cv
        
        cv2.imshow(SCREENSHOT_WINDOW_NAME, display_img)
        cv2.waitKey(1)
        
        # Optionally save to disk (full resolution)
        if SCREENSHOT_SAVE_DIR:
            os.makedirs(SCREENSHOT_SAVE_DIR, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}_action{action_num or 0}.png"
            cv2.imwrite(os.path.join(SCREENSHOT_SAVE_DIR, filename), img_cv)
    
    return screenshot_b64

# === TOOL DEFINITIONS ===
BROWSER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": "Click at specific coordinates. MUST provide BOTH x and y coordinates as bounding boxes: x: [x1, x2], y: [y1, y2]. The click will happen at the center of the bounding box.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "description": "X coordinates as [x1, x2] bounding box",
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 2,
                        "maxItems": 2
                    },
                    "y": {
                        "description": "Y coordinates as [y1, y2] bounding box",
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 2,
                        "maxItems": 2
                    }
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text into currently focused element",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a keyboard key (Enter, Tab, Escape, Backspace, Delete, ArrowUp, ArrowDown, ArrowLeft, ArrowRight)",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key to press"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll the page up or down",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string", 
                        "enum": ["up", "down"],
                        "description": "Scroll direction"
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Pixels to scroll (default 300)",
                        "default": 300
                    }
                },
                "required": ["direction"]
            }
        }
    }
]

def brain():
    open_browser()
    open_url("https://google.com")

    SYSTEM_PROMPT = """You are a browser automation agent. You can see the current screen and previous screenshots showing what happened.

        CRITICAL: When clicking, you MUST provide BOTH x AND y coordinates in this exact format:
        {
        "x": [x1, x2],
        "y": [y1, y2]
        }

        For example, to click a button at bounding box x: 396-476, y: 200-240:
        {
        "x": [396, 476],
        "y": [200, 240]
        }

        The system will automatically click at the center of the bounding box.
        Execute actions step by step to accomplish the user's goal.

        You will receive:
        - Previous screenshots showing the history of actions (labeled with what action was taken)
        - The current screenshot showing the present state
        Use this context to understand what has been tried and what to do next."""
    
    prompt = "apply for software jobs on linkedin and when you are on linkedin, click on apply blue button for jobs"
    signals_from_hand = []
    max_actions = 15
    images_list = []

    for i in range(max_actions):
        screenshot_b64 = take_screenshot(action_num=i+1)
        
        images_list.append(screenshot_b64)


        STATE_FULL_PROMPT = f"""GOAL: {prompt} Previous Actions: {chr(10).join([f"{idx+1}. {action}" for idx, action in enumerate(signals_from_hand)]) if signals_from_hand else "None"} Looking at the CURRENT screenshot (the last image), what is the NEXT action to take?"""

        row_signals_from_brain = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "qwen3-vl:30b",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": STATE_FULL_PROMPT,
                        "images": images_list
                    }
                ],
                "tools": BROWSER_TOOLS,
                "stream": False
            },
            timeout=180
        ).json()
        
        less_row_brain_signals = row_signals_from_brain.get("message", {}).get("tool_calls", [])
        if not less_row_brain_signals:
            print("No tool calls - task complete or stuck")
            continue
            
        organ = less_row_brain_signals[0]["function"]["name"]
        print("organ: ",organ)
        organ_signals = less_row_brain_signals[0]["function"].get("arguments", {})
        print("organ_signals: ",organ_signals)


        if isinstance(organ_signals, str):
            organ_signals = json.loads(organ_signals)
        
        hands = globals().get(organ)
        result = hands(**organ_signals)
        
        signals_from_hand.append(result)
            
        

if __name__ == "__main__":    
    brain()