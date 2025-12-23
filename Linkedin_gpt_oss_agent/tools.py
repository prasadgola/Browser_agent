import asyncio
import json
import random
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

PROMPT = "Find software engineer jobs"

# --- PROMPTS ---

SYSTEM_PROMPT = """You have job application web page elements and you have to apply for jobs.
"""

# --- BROWSER TOOLS SCHEMA ---

BROWSER_TOOLS = [
    {"type": "function", "function": {"name": "click", "description": "Click element by index", "parameters": {"type": "object", "properties": {"index": {"type": "integer"}}, "required": ["index"]}}},
]

 # {"type": "function", "function": {"name": "type_text", "description": "Type text and press Enter", "parameters": {"type": "object", "properties": {"index": {"type": "integer"}, "text": {"type": "string"}}, "required": ["index", "text"]}}},
_driver = None
_elements_cache = {}

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
    return f"Opened {url}"



async def type_text(index, text):
    if index not in _elements_cache:
        return f"Invalid index {index}"
    
    element_info = _elements_cache[index]
    automation_id = element_info['automationId']
    iframe_idx = element_info.get('iframe')
    
    try:
        # Switch to iframe if needed
        if iframe_idx is not None:
            iframes = _driver.find_elements(By.TAG_NAME, "iframe")
            _driver.switch_to.frame(iframes[iframe_idx])
        
        # Find the element
        element = _driver.execute_script(f"""
            return document.querySelector('[data-automation-id="{automation_id}"]');
        """)
        
        if not element:
            _driver.switch_to.default_content()
            return f"Element not found for index {index}"
        
        # Click to focus
        _driver.execute_script("arguments[0].click(); arguments[0].focus();", element)
        await asyncio.sleep(0.5)
        
        # Clear existing text
        _driver.execute_script("arguments[0].value = '';", element)
        
        # Type character by character with human-like delays
        for char in text:
            element.send_keys(char)
            await asyncio.sleep(random.uniform(0.02, 0.08))
        
        # Press Enter
        element.send_keys(Keys.ENTER)
        
        # Switch back to main frame
        _driver.switch_to.default_content()
        
        await asyncio.sleep(2)
        return f"Typed '{text}' into index {index}"
        
    except Exception as e:
        _driver.switch_to.default_content()
        return f"Type error: {str(e)[:100]}"

async def press_key(key: str) -> str:
    global driver
    
    try:
        # Find the active/focused element and send key to it
        active = driver.switch_to.active_element
        
        key_map = {
            "enter": Keys.ENTER,
            "tab": Keys.TAB,
            "escape": Keys.ESCAPE,
            "backspace": Keys.BACKSPACE,
            "down": Keys.ARROW_DOWN,
            "up": Keys.ARROW_UP,
        }
        
        active.send_keys(key_map.get(key.lower(), key))
        time.sleep(0.3)
        return f"✓ Pressed {key}"
    except Exception as e:
        return f"✗ Failed: {str(e)}"































async def click(index):
    """Click element by index - handles main frame, iframes, and shadow DOM"""
    if index not in _elements_cache:
        return f"Invalid index {index}"
    
    # print("clicking:")
    
    # print(_elements_cache)
    # print("================================================================================================================================================\n")
    
    element_info = _elements_cache[index]
    automation_id = element_info['automationId']
    iframe_idx = element_info.get('iframe')
    
    try:
        # Switch to iframe if needed
        if iframe_idx is not None:
            iframes = _driver.find_elements(By.TAG_NAME, "iframe")
            if iframe_idx >= len(iframes):
                return f"Iframe {iframe_idx} not found"
            _driver.switch_to.frame(iframes[iframe_idx])
        
        # Find element (handles both regular DOM and shadow DOM)
        element = _driver.execute_script(f"""
            function findElement(root) {{
                // Try regular DOM first
                let el = root.querySelector('[data-automation-id="{automation_id}"]');
                if (el) return el;
                
                // Search shadow DOM recursively
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT);
                let node;
                while (node = walker.nextNode()) {{
                    if (node.shadowRoot) {{
                        el = findElement(node.shadowRoot);
                        if (el) return el;
                    }}
                }}
                return null;
            }}
            return findElement(document.body);
        """)
        
        if not element:
            _driver.switch_to.default_content()
            return f"Element {automation_id} not found"
        
        # Scroll into view and click
        _driver.execute_script("""
            arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});
            arguments[0].click();
        """, element)
        
        _driver.switch_to.default_content()
        await asyncio.sleep(2)
        
        return f"Clicked [{index}] {element_info['text'][:30]}"
        
    except Exception as e:
        _driver.switch_to.default_content()
        return f"Click error: {str(e)[:100]}"



























































    































































































































































































async def get_page_state():
    global _elements_cache
    _elements_cache = {}
    
    try:
        viewport_width = _driver.execute_script("return window.innerWidth;")
        center_threshold = viewport_width * 0.5
    except:
        center_threshold = 960
    
    iframes = _driver.find_elements(By.TAG_NAME, "iframe")

    # print(_driver.find_elements(By.XPATH, "//*"))

    
    state_parts = []
    idx = 0
    
    # ===== MAIN FRAME =====
    for tag in ['button', 'a', 'input', 'select', 'textarea', 'h1', 'h2', 'h3', 'label']:
        for element in _driver.find_elements(By.TAG_NAME, tag):
            try:
                if not element.is_displayed():
                    continue
                
                text = (element.text or element.get_attribute('aria-label') or element.get_attribute('value') or '').strip()
                
                if not element.get_attribute('data-automation-id'):
                    automation_id = f'main-{tag}-{idx}-{random.random()}'
                    # print("no automation_id: ")
                    _driver.execute_script(f"arguments[0].setAttribute('data-automation-id', '{automation_id}');", element)
                else:
                    # print("automation_id")
                    automation_id = element.get_attribute('data-automation-id')
                
                extra = get_element_context(element, tag)
                
                _elements_cache[idx] = {
                    'automationId': automation_id,
                    'iframe': None,
                    'text': text[:60]
                }

                # print(automation_id)
                
                loc = element.location
                x = loc['x'] + element.size['width'] // 2
                side = "RIGHT" if x > center_threshold else "LEFT"
                
                state_parts.append(f"[{idx}] ({side}) {extra}: {text[:60]}")
                idx += 1
            except:
                continue
    
    # ===== IFRAMES =====
    for iframe_idx, iframe in enumerate(iframes):
        try:
            _driver.switch_to.frame(iframe)
            
            for tag in ['button', 'a', 'input', 'select', 'textarea', 'h1', 'h2', 'h3', 'label']:
                for element in _driver.find_elements(By.TAG_NAME, tag):
                    try:
                        if not element.is_displayed():
                            continue
                        
                        text = (element.text or element.get_attribute('aria-label') or element.get_attribute('value') or '').strip()
                        
                        if not element.get_attribute('data-automation-id'):
                            # print("no automation_id")
                            automation_id = f'iframe{iframe_idx}-{tag}-{idx}-{random.random()}'
                            _driver.execute_script(f"arguments[0].setAttribute('data-automation-id', '{automation_id}');", element)
                        else:
                            # print("automation_id")
                            automation_id = element.get_attribute('data-automation-id')
                        
                        extra = get_element_context(element, tag)
                        
                        _elements_cache[idx] = {
                            'automationId': automation_id,
                            'iframe': iframe_idx,
                            'text': text[:60]
                        }
                        
                        loc = element.location
                        x = loc['x'] + element.size['width'] // 2
                        side = "RIGHT" if x > center_threshold else "LEFT"
                        # print(automation_id)                      
                        state_parts.append(f"[{idx}] ({side}) {extra}: {text[:60]}")
                        idx += 1
                    except:
                        continue
            
            _driver.switch_to.default_content()
        except:
            _driver.switch_to.default_content()
            continue
    
    # ===== SHADOW DOM =====
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
                    const text = (node.innerText || node.textContent || node.getAttribute('aria-label') || node.getAttribute('value') || '').trim();
                    const rect = node.getBoundingClientRect();
                    const style = window.getComputedStyle(node);
                    
                    const isVisible = style.display !== 'none' && 
                                     style.visibility !== 'hidden' && 
                                     style.opacity !== '0';
                    
                    if ((text || node.tagName === 'INPUT') && isVisible) {
                        if (!node.getAttribute('data-automation-id')) {
                            node.setAttribute('data-automation-id', 'shadow-' + Date.now() + '-' + Math.random());
                        }
                        
                        elements.push({
                            tag: node.tagName,
                            text: text.substring(0, 80),
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            automationId: node.getAttribute('data-automation-id'),
                            type: node.getAttribute('type') || '',
                            placeholder: node.getAttribute('placeholder') || '',
                            name: node.getAttribute('name') || '',
                            required: node.hasAttribute('required'),
                            disabled: node.disabled || false,
                            href: node.getAttribute('href') || ''
                        });
                    }
                }
            }
            
            return elements;
        }
        
        return getAllElements(document.body);
    """)

    for el_data in shadow_elements:
        x, y = el_data['x'], el_data['y']
        
        if abs(x) > 5000 or abs(y) > 5000:
            continue
        
        _elements_cache[idx] = {
            'automationId': el_data['automationId'],
            'iframe': None,
            'text': el_data['text']
        }
        
        side = "RIGHT" if x > center_threshold else "LEFT"
        
        extra = format_shadow_context(el_data)
        
        state_parts.append(f"[{idx}] ({side}) {extra}: {el_data['text']}")
        idx += 1
    # print(automation_id)  
    # ===== PAGE SUMMARY =====
    if not state_parts:
        return "No elements"

    # print("================================================================================================================================================\n")
    
    # print("hello")
    # print(_elements_cache)
    
    return "\n".join(state_parts)


def get_element_context(element, tag):
    """Get context for main frame and iframe elements"""
    try:
        if tag == 'input':
            input_type = element.get_attribute('type') or 'text'
            placeholder = element.get_attribute('placeholder') or ''
            required = ' (REQUIRED)' if element.get_attribute('required') else ''
            
            desc = f"INPUT[{input_type}]{required}"
            if placeholder:
                desc += f" placeholder='{placeholder[:30]}'"
            return desc
            
        elif tag == 'button':
            disabled = ' (DISABLED)' if not element.is_enabled() else ''
            return f"BUTTON{disabled}"
            
        elif tag == 'a':
            href = element.get_attribute('href') or ''
            external = ' (EXTERNAL)' if href and 'linkedin.com' not in href else ''
            return f"LINK{external}"
    except:
        pass
    
    return tag.upper()


def format_shadow_context(el_data):
    """Format context for shadow DOM elements"""
    tag = el_data['tag']
    
    if tag == 'INPUT':
        input_type = el_data.get('type', 'text')
        placeholder = el_data.get('placeholder', '')
        required = ' (REQUIRED)' if el_data.get('required') else ''
        
        desc = f"INPUT[{input_type}]{required}"
        if placeholder:
            desc += f" placeholder='{placeholder[:30]}'"
        return desc
        
    elif tag == 'BUTTON':
        disabled = ' (DISABLED)' if el_data.get('disabled') else ''
        return f"BUTTON{disabled}"
        
    elif tag == 'A':
        href = el_data.get('href', '')
        external = ' (EXTERNAL)' if href and 'linkedin.com' not in href else ''
        return f"LINK{external}"

    
    return tag
