import os
import time
import ollama
import base64
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains

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

def click_at(x, y):
    global driver
    show_click_indicator(x, y, "red")
    time.sleep(0.3)
    ActionChains(driver).move_by_offset(x, y).click().perform()
    ActionChains(driver).move_by_offset(-x, -y).perform()  # reset position
    time.sleep(0.3)

def brain():
    global driver
    open_browser()
    open_url("https://google.com")

    while True:
        screenshot_b64 = driver.get_screenshot_as_png()
        screenshot_b64 = base64.b64encode(screenshot_b64).decode('utf-8')
        viewport = driver.execute_script("return {width: window.innerWidth, height: window.innerHeight}")
        target = "search bar"
        prompt = f"""Look at this browser screenshot. The viewport is {viewport['width']}x{viewport['height']} pixels.

        Find the {target} and return its center coordinates.

        Return ONLY valid JSON in this exact format, nothing else:
        {{"found": true, "x": 640, "y": 350, "element": "description of element"}}

        If not found:
        {{"found": false, "x": 0, "y": 0, "element": "not found"}}"""

        response = ollama.chat(
            model='gemma3:27b',
            messages=[{
                'role': 'user',
                'content': prompt,
                'images': [screenshot_b64]
            }]
        )

        result_text = response['message']['content']
        start = result_text.find('{')
        end = result_text.rfind('}') + 1
        if start != -1 and end > start:
            json_str = result_text[start:end]
            result2 = json.loads(json_str)
        else:
            result2 = None
    
        print(result2)
        click_at(result2['x'], result2['y'])

if __name__ == "__main__":    
    brain()