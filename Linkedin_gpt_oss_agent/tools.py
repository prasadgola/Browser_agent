import asyncio
import json
import random
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

PROMPT = "Find 'software engineer' jobs in New York and click on the first listing."

# --- PROMPTS ---

SYSTEM_PROMPT = """You are a LinkedIn automation agent.

CRITICAL RULES:
1. Job listings are on the LEFT side (indices 26, 28, 30, 42, 44, etc.) - these have company names
2. Search suggestions are on the RIGHT (indices 34-37) - DO NOT CLICK THESE
3. To view a job's details and "Easy Apply" button, click a LEFT job listing
4. After clicking a job, wait for the right panel to load, then look for "Easy Apply" button
5. The search bar is index 3 (INPUT)

WORKFLOW:
- Search: type_text at index 3
- View job: click on LEFT job listing (26, 28, 30, etc.)
- Apply: After job details load, click "Easy Apply" button that appears on RIGHT"""

# --- BROWSER TOOLS SCHEMA ---

BROWSER_TOOLS = [
    {"type": "function", "function": {"name": "click", "description": "Click element by index", "parameters": {"type": "object", "properties": {"index": {"type": "integer"}}, "required": ["index"]}}},
    {"type": "function", "function": {"name": "type_text", "description": "Type text and press Enter", "parameters": {"type": "object", "properties": {"index": {"type": "integer"}, "text": {"type": "string"}}, "required": ["index", "text"]}}},
    {"type": "function", "function": {"name": "scroll", "description": "Scroll LEFT or RIGHT pane", "parameters": {"type": "object", "properties": {"side": {"type": "string", "enum": ["LEFT", "RIGHT"]}, "direction": {"type": "string", "enum": ["up", "down"]}}, "required": ["side", "direction"]}}},
    {"type": "function", "function": {"name": "wait", "description": "Wait for elements to load", "parameters": {"type": "object", "properties": {"seconds": {"type": "integer"}}, "required": ["seconds"]}}}
]

_driver = None
_elements_cache = {}

async def debug_page():
    """Find what selectors LinkedIn actually uses"""
    result = _driver.execute_script("""
        return {
            // Check various possible right panel selectors
            panels: {
                'jobs-search__job-details': !!document.querySelector('.jobs-search__job-details'),
                'jobs-details': !!document.querySelector('.jobs-details'),
                'job-details-pane': !!document.querySelector('.job-details-pane'),
                'artdeco-card': document.querySelectorAll('.artdeco-card').length,
                'scaffold-layout__detail': !!document.querySelector('.scaffold-layout__detail')
            },
            
            // Get all main containers
            containers: Array.from(document.querySelectorAll('[class*="job"]')).slice(0,10).map(el => ({
                class: el.className.substring(0,60),
                hasText: el.innerText?.length > 50
            })),
            
            // Check if Easy Apply exists anywhere
            easyApply: Array.from(document.querySelectorAll('button, [role="button"]'))
                .filter(el => el.innerText?.toLowerCase().includes('apply'))
                .map(el => el.innerText?.substring(0,40)),
                
            // Page structure
            pageUrl: window.location.href,
            bodyText: document.body.innerText.substring(0, 200)
        }
    """)
    print(f"\n=== PAGE DEBUG ===")
    print(f"Panels: {result['panels']}")
    print(f"Containers: {result['containers'][:3]}")
    print(f"Apply buttons: {result['easyApply']}")
    print(f"URL: {result['pageUrl']}")
    print(f"Body preview: {result['bodyText'][:100]}")
    print(f"==================\n")
    return str(result)



async def open_browser() -> str:
    global _driver
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    # LinkedIn uses window dimensions to fingerprint bots
    options.add_argument('--window-size=1920,1080')
    profile_path = os.path.expanduser('~/AI Studio/chrome_automation_profile')
    _driver = uc.Chrome(options=options, user_data_dir=profile_path)
    return "Browser opened"

async def open_url(url: str) -> str:
    _driver.get(url)
    await asyncio.sleep(8) 
    return f"Opened {url}"

async def click(index):
    try:
        # Check if this is an iframe button
        if index in _elements_cache:
            # Try clicking in iframe first
            iframes = _driver.find_elements(By.TAG_NAME, "iframe")
            
            for iframe in iframes:
                try:
                    _driver.switch_to.frame(iframe)
                    buttons = _driver.find_elements(By.TAG_NAME, "button")
                    
                    for btn in buttons:
                        text = (btn.text or btn.get_attribute('aria-label') or '').lower()
                        if 'apply' in text and index < len(buttons):
                            btn.click()
                            await asyncio.sleep(3)
                            _driver.switch_to.default_content()
                            return f"Clicked Apply button in iframe"
                    
                    _driver.switch_to.default_content()
                except:
                    _driver.switch_to.default_content()
                    continue
        
        # Fallback to coordinate click in main frame
        elements = _driver.find_elements(By.CSS_SELECTOR, "button, a[href], input, [role='button']")
        
        if index >= len(elements):
            return f"Index {index} out of range"
        
        el = elements[index]
        el.click()
        await asyncio.sleep(3)
        
        return f"Clicked index {index}"
    except Exception as e:
        return f"Click error: {str(e)[:100]}"



async def type_text(index, text):
    await click(index)
    actions = ActionChains(_driver)
    # Physical clear: Ctrl/Cmd+A then Backspace
    cmd = Keys.COMMAND if os.uname().sysname == 'Darwin' else Keys.CONTROL
    actions.key_down(cmd).send_keys('a').key_up(cmd).send_keys(Keys.BACKSPACE).perform()
    
    for char in text:
        actions.send_keys(char)
        actions.pause(random.uniform(0.02, 0.08))
    actions.send_keys(Keys.ENTER).perform()
    return f"Typed {text}"

async def scroll(side, direction):
    # Match the rehydrated LazyColumn containers in your HTML
    selector = ".jobs-search-results-list" if side == "LEFT" else ".jobs-search__job-details"
    amount = 600 if direction == "down" else -600
    js = f"const e = document.querySelector('{selector}'); if(e) e.scrollBy(0, {amount}); else window.scrollBy(0, {amount});"
    _driver.execute_script(js)
    await asyncio.sleep(1)
    return f"Scrolled {side} {direction}"

async def wait(seconds):
    await asyncio.sleep(int(seconds))
    return f"Waited {seconds}s"




































































































async def get_page_state():
    global _elements_cache
    _elements_cache = {}
    
    await asyncio.sleep(3)
    
    # Check for iframes
    iframes = _driver.find_elements(By.TAG_NAME, "iframe")
    print(f"Found {len(iframes)} iframes")
    
    apply_buttons = []
    
    # Search in main document
    for btn in _driver.find_elements(By.TAG_NAME, "button"):
        try:
            text = (btn.text or btn.get_attribute('aria-label') or '').lower()
            if 'apply' in text:
                loc = btn.location
                size = btn.size
                apply_buttons.append({
                    'text': text[:60],
                    'x': loc['x'] + size['width'] // 2,
                    'y': loc['y'] + size['height'] // 2,
                    'source': 'main'
                })
        except:
            continue
    
    # Search in each iframe
    for i, iframe in enumerate(iframes):
        try:
            _driver.switch_to.frame(iframe)
            for btn in _driver.find_elements(By.TAG_NAME, "button"):
                try:
                    text = (btn.text or btn.get_attribute('aria-label') or '').lower()
                    if 'apply' in text:
                        loc = btn.location
                        size = btn.size
                        apply_buttons.append({
                            'text': text[:60],
                            'x': loc['x'] + size['width'] // 2,
                            'y': loc['y'] + size['height'] // 2,
                            'source': f'iframe-{i}'
                        })
                except:
                    continue
            _driver.switch_to.default_content()
        except:
            _driver.switch_to.default_content()
            continue
    
    print(f"Apply buttons found: {len(apply_buttons)} from {[b['source'] for b in apply_buttons]}")
    
    # Get shadow DOM elements (back in main frame)
    shadow_elements = _driver.execute_script("""
        function getAllElements(root) {
            let elements = [];
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
            let node;
            
            while (node = walker.nextNode()) {
                if (node.shadowRoot) {
                    elements = elements.concat(getAllElements(node.shadowRoot));
                }
                
                if (node.tagName === 'BUTTON' || node.tagName === 'A' || node.tagName === 'INPUT') {
                    const text = (node.innerText || node.textContent || node.getAttribute('aria-label') || '').trim();
                    const rect = node.getBoundingClientRect();
                    const style = window.getComputedStyle(node);
                    
                    const isVisible = style.display !== 'none' && 
                                     style.visibility !== 'hidden' && 
                                     style.opacity !== '0';
                    
                    if ((text || node.tagName === 'INPUT') && isVisible) {
                        elements.push({
                            tag: node.tagName,
                            text: text.substring(0, 80),
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2
                        });
                    }
                }
            }
            
            return elements;
        }
        
        return getAllElements(document.body);
    """)
    
    try:
        viewport_width = _driver.execute_script("return window.innerWidth;")
        center_threshold = viewport_width * 0.5
    except:
        center_threshold = 960
    
    state_parts = []
    idx = 0
    
    # Add Apply buttons FIRST
    for btn_data in apply_buttons:
        _elements_cache[idx] = (btn_data['x'], btn_data['y'])
        state_parts.append(f"[{idx}] (RIGHT) BUTTON: {btn_data['text']} [{btn_data['source']}] ⭐⭐⭐")
        idx += 1
    
    # Add shadow DOM elements
    for el_data in shadow_elements:
        x, y = el_data['x'], el_data['y']
        
        if abs(x) > 5000 or abs(y) > 5000:
            continue
        
        _elements_cache[idx] = (x, y)
        side = "RIGHT" if x > center_threshold else "LEFT"
        state_parts.append(f"[{idx}] ({side}) {el_data['tag']}: {el_data['text']}")
        idx += 1
    
    return "\n".join(state_parts) if state_parts else "No elements"