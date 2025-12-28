import asyncio
import json
import random
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

PROMPT = """ post hi, reply hello, reply bye, reply goodbye
"""

SYSTEM_PROMPT = """
You are X browser expert in posting
"""


# --- BROWSER TOOLS SCHEMA ---

BROWSER_TOOLS = [
    {"type": "function", "function": {"name": "click", "description": "Click element by index", "parameters": {"type": "object", "properties": {"index": {"type": "integer"}}, "required": ["index"]}}},
    {"type": "function", "function": {"name": "type_text", "description": "Type text and press Enter", "parameters": {"type": "object", "properties": {"index": {"type": "integer"}, "text": {"type": "string"}}, "required": ["index", "text"]}}}
]

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
    global _elements_cache, _driver
    
    element_info = _elements_cache.get(index)
    if not element_info:
        print(f"ERROR: Index {index} not in cache")
        return f"Error: Index {index} not found"  # Return string, not None
    
    automation_id = element_info['automationId']
    print(f"DEBUG: Looking for element with automation_id: {automation_id}")
    
    try:
        # Find element
        element = _driver.find_element(By.CSS_SELECTOR, f'[data-automation-id="{automation_id}"]')
        print(f"DEBUG: Found element: {element.tag_name}")
        
        # Click it
        element.click()
        print("DEBUG: Clicked element")
        time.sleep(0.3)
        
        # Get active element and send keys
        active = _driver.switch_to.active_element
        print(f"DEBUG: Active element: {active.tag_name}")
        
        active.send_keys(text)
        print(f"DEBUG: Sent keys: {text}")
        
        return f"type_text {{'index': {index}, 'text': '{text}'}}"  # Return string
        
    except Exception as e:
        print(f"ERROR: {e}")
        return f"Error typing: {e}"  # Return string, not None

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

async def upload_file(index, filename="basavaprasad_resume.pdf"):
    """Upload a file - handles LinkedIn's hidden file inputs"""
    if index not in _elements_cache:
        return f"Invalid index {index}"
    
    element_info = _elements_cache[index]
    iframe_idx = element_info.get('iframe')
    
    # Get absolute path - look in current directory and common locations
    possible_paths = [
        os.path.abspath(filename),
        os.path.join(os.path.dirname(__file__), filename),
        os.path.expanduser(f"~/AI Studio/{filename}"),
    ]
    
    file_path = None
    for p in possible_paths:
        if os.path.exists(p):
            file_path = p
            break
    
    if not file_path:
        return f"File not found: {filename}"
    
    try:
        # Switch to iframe if needed
        if iframe_idx is not None:
            iframes = _driver.find_elements(By.TAG_NAME, "iframe")
            _driver.switch_to.frame(iframes[iframe_idx])
        
        # LinkedIn hides file inputs - find ANY file input on the page and make it visible
        file_input = _driver.execute_script("""
            const inputs = document.querySelectorAll('input[type="file"]');
            if (inputs.length > 0) {
                // Make it interactable
                inputs[0].style.display = 'block';
                inputs[0].style.visibility = 'visible';
                inputs[0].style.opacity = '1';
                inputs[0].style.position = 'relative';
                inputs[0].style.width = '100px';
                inputs[0].style.height = '100px';
                return inputs[0];
            }
            return null;
        """)
        
        if file_input:
            file_input.send_keys(file_path)
            _driver.switch_to.default_content()
            await asyncio.sleep(2)
            return f"Uploaded {filename}"
        
        _driver.switch_to.default_content()
        return "No file input found on page"
        
    except Exception as e:
        _driver.switch_to.default_content()
        return f"Upload error: {str(e)[:100]}"

async def click(index):
    """Click element by index - handles main frame, iframes, and shadow DOM"""
    if index not in _elements_cache:
        return f"Invalid index {index}"
    
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
        popup_data = _driver.execute_script("""
            // Check if reply popup is open by looking for Close + Drafts buttons together
            const closeBtn = Array.from(document.querySelectorAll('button')).find(b => 
                b.innerText.trim() === 'Close' || b.getAttribute('aria-label') === 'Close');
            const draftsBtn = Array.from(document.querySelectorAll('button')).find(b => 
                b.innerText.trim() === 'Drafts');
            
            if (!closeBtn || !draftsBtn) return null;
            
            // Popup is open! Find the popup container
            let popup = closeBtn.parentElement;
            for (let i = 0; i < 10; i++) {
                if (!popup) break;
                if (popup.querySelector('[contenteditable="true"]') || popup.querySelector('[role="textbox"]')) {
                    break;
                }
                popup = popup.parentElement;
            }
            
            if (!popup) return null;
            
            // Get all interactive elements inside popup
            const elements = [];
            
            // Buttons
            popup.querySelectorAll('button').forEach(el => {
                if (!el.offsetParent) return; // not visible
                const rect = el.getBoundingClientRect();
                const text = (el.innerText || el.getAttribute('aria-label') || '').trim();
                const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true';
                const id = 'popup-btn-' + Math.random();
                el.setAttribute('data-automation-id', id);
                elements.push({
                    type: 'button',
                    text: text.substring(0, 50),
                    disabled: disabled,
                    automationId: id,
                    x: rect.left + rect.width / 2
                });
            });
            
            // Contenteditable (reply box)
            const replyBox = popup.querySelector('[contenteditable="true"]') || popup.querySelector('[role="textbox"]');
            if (replyBox) {
                const rect = replyBox.getBoundingClientRect();
                const id = 'reply-box-' + Math.random();
                replyBox.setAttribute('data-automation-id', id);
                elements.push({
                    type: 'reply_box',
                    text: (replyBox.innerText || '').trim().substring(0, 50),
                    automationId: id,
                    x: rect.left + rect.width / 2
                });
            }
            
            return elements;
        """)
        
        if popup_data and len(popup_data) > 0:
            print("DEBUG: Reply popup detected! Returning only popup elements.")
            
            state_parts = []
            idx = 0
            viewport_width = _driver.execute_script("return window.innerWidth;")
            center_threshold = viewport_width * 0.5
            
            for el in popup_data:
                side = "RIGHT" if el['x'] > center_threshold else "LEFT"
                
                if el['type'] == 'reply_box':
                    display_text = el['text'] if el['text'] else "(empty)"
                    state_parts.append(f"[{idx}] ({side}) REPLY_BOX placeholder='Post your reply': {display_text}")
                    _elements_cache[idx] = {
                        'automationId': el['automationId'],
                        'iframe': None,
                        'text': el['text'],
                        'isContentEditable': True
                    }
                else:
                    disabled = ' (DISABLED)' if el.get('disabled') else ''
                    state_parts.append(f"[{idx}] ({side}) BUTTON{disabled}: {el['text']}")
                    _elements_cache[idx] = {
                        'automationId': el['automationId'],
                        'iframe': None,
                        'text': el['text'],
                        'isContentEditable': False
                    }
                idx += 1
            
            return "\n".join(state_parts)
            
    except Exception as e:
        print(f"Popup detection error: {e}")
   
   
    try:
        viewport_width = _driver.execute_script("return window.innerWidth;")
        center_threshold = viewport_width * 0.5
    except:
        center_threshold = 960
    
    iframes = _driver.find_elements(By.TAG_NAME, "iframe")
    
    state_parts = []
    idx = 0
    
    # Track already-processed automation IDs to avoid duplicates
    processed_ids = set()
    
    # ===== MAIN FRAME - STANDARD ELEMENTS =====
    for tag in ['button', 'a', 'input', 'select', 'textarea', 'h1', 'h2', 'h3', 'label']:
        for element in _driver.find_elements(By.TAG_NAME, tag):
            try:
                if not element.is_displayed():
                    continue
                
                text = (element.text or element.get_attribute('aria-label') or element.get_attribute('value') or '').strip()
                
                if not element.get_attribute('data-automation-id'):
                    automation_id = f'main-{tag}-{idx}-{random.random()}'
                    _driver.execute_script(f"arguments[0].setAttribute('data-automation-id', '{automation_id}');", element)
                else:
                    automation_id = element.get_attribute('data-automation-id')
                
                if automation_id in processed_ids:
                    continue
                processed_ids.add(automation_id)
                
                extra = get_element_context(element, tag)
                
                _elements_cache[idx] = {
                    'automationId': automation_id,
                    'iframe': None,
                    'text': text[:60],
                    'isContentEditable': False
                }
                
                loc = element.location
                x = loc['x'] + element.size['width'] // 2
                side = "RIGHT" if x > center_threshold else "LEFT"
                
                state_parts.append(f"[{idx}] ({side}) {extra}: {text}")
                idx += 1
            except:
                continue


    try:
        contenteditable_elements = _driver.find_elements(
            By.CSS_SELECTOR, 
            '[contenteditable="true"], [role="textbox"]:not(input):not(textarea)'
        )
        
        for element in contenteditable_elements:
            try:
                if not element.is_displayed():
                    continue
                
                # Skip if it's already a standard input/textarea
                tag_name = element.tag_name.lower()
                if tag_name in ['input', 'textarea']:
                    continue
                
                text = (element.text or '').strip()
                aria_label = element.get_attribute('aria-label') or ''
                data_placeholder = element.get_attribute('data-placeholder') or ''
                placeholder = element.get_attribute('placeholder') or ''
                role = element.get_attribute('role') or ''
                
                if not element.get_attribute('data-automation-id'):
                    automation_id = f'contenteditable-{idx}-{random.random()}'
                    _driver.execute_script(f"arguments[0].setAttribute('data-automation-id', '{automation_id}');", element)
                else:
                    automation_id = element.get_attribute('data-automation-id')
                
                if automation_id in processed_ids:
                    continue
                processed_ids.add(automation_id)
                
                _elements_cache[idx] = {
                    'automationId': automation_id,
                    'iframe': None,
                    'text': text[:60],
                    'isContentEditable': True
                }
                
                loc = element.location
                x = loc['x'] + element.size['width'] // 2
                side = "RIGHT" if x > center_threshold else "LEFT"
                
                # Build descriptive label
                hint = data_placeholder or placeholder or aria_label or ''
                if hint:
                    desc = f"COMPOSE_BOX placeholder='{hint[:40]}'"
                else:
                    desc = "COMPOSE_BOX"
                
                display_text = text[:30] if text else "(empty)"
                
                state_parts.append(f"[{idx}] ({side}) {desc}: {display_text}")
                idx += 1
            except:
                continue
    except Exception as e:
        print(f"Error detecting contenteditable: {e}")
    
    # ===== IFRAMES =====
    for iframe_idx, iframe in enumerate(iframes):
        try:
            _driver.switch_to.frame(iframe)
            
            # Standard elements in iframe
            for tag in ['button', 'a', 'input', 'select', 'textarea', 'h1', 'h2', 'h3', 'label']:
                for element in _driver.find_elements(By.TAG_NAME, tag):
                    try:
                        if not element.is_displayed():
                            continue
                        
                        text = (element.text or element.get_attribute('aria-label') or element.get_attribute('value') or '').strip()
                        
                        if not element.get_attribute('data-automation-id'):
                            automation_id = f'iframe{iframe_idx}-{tag}-{idx}-{random.random()}'
                            _driver.execute_script(f"arguments[0].setAttribute('data-automation-id', '{automation_id}');", element)
                        else:
                            automation_id = element.get_attribute('data-automation-id')
                        
                        if automation_id in processed_ids:
                            continue
                        processed_ids.add(automation_id)
                        
                        extra = get_element_context(element, tag)
                        
                        _elements_cache[idx] = {
                            'automationId': automation_id,
                            'iframe': iframe_idx,
                            'text': text[:60],
                            'isContentEditable': False
                        }
                        
                        loc = element.location
                        x = loc['x'] + element.size['width'] // 2
                        side = "RIGHT" if x > center_threshold else "LEFT"
                        
                        state_parts.append(f"[{idx}] ({side}) {extra}: {text}")
                        idx += 1
                    except:
                        continue
            
            # Contenteditable elements in iframe
            try:
                contenteditable_in_iframe = _driver.find_elements(
                    By.CSS_SELECTOR, 
                    '[contenteditable="true"], [role="textbox"]:not(input):not(textarea)'
                )
                
                for element in contenteditable_in_iframe:
                    try:
                        if not element.is_displayed():
                            continue
                        
                        tag_name = element.tag_name.lower()
                        if tag_name in ['input', 'textarea']:
                            continue
                        
                        text = (element.text or '').strip()
                        aria_label = element.get_attribute('aria-label') or ''
                        data_placeholder = element.get_attribute('data-placeholder') or ''
                        placeholder = element.get_attribute('placeholder') or ''
                        
                        if not element.get_attribute('data-automation-id'):
                            automation_id = f'iframe{iframe_idx}-contenteditable-{idx}-{random.random()}'
                            _driver.execute_script(f"arguments[0].setAttribute('data-automation-id', '{automation_id}');", element)
                        else:
                            automation_id = element.get_attribute('data-automation-id')
                        
                        if automation_id in processed_ids:
                            continue
                        processed_ids.add(automation_id)
                        
                        _elements_cache[idx] = {
                            'automationId': automation_id,
                            'iframe': iframe_idx,
                            'text': text[:60],
                            'isContentEditable': True
                        }
                        
                        loc = element.location
                        x = loc['x'] + element.size['width'] // 2
                        side = "RIGHT" if x > center_threshold else "LEFT"
                        
                        hint = data_placeholder or placeholder or aria_label or ''
                        if hint:
                            desc = f"COMPOSE_BOX placeholder='{hint[:40]}'"
                        else:
                            desc = "COMPOSE_BOX"
                        
                        display_text = text[:30] if text else "(empty)"
                        
                        state_parts.append(f"[{idx}] ({side}) {desc}: {display_text}")
                        idx += 1
                    except:
                        continue
            except:
                pass
            
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
                
                const isInteractive = node.tagName === 'BUTTON' || 
                                     node.tagName === 'A' || 
                                     node.tagName === 'INPUT' ||
                                     node.tagName === 'TEXTAREA' ||
                                     node.tagName === 'SELECT' ||
                                     node.getAttribute('contenteditable') === 'true' ||
                                     node.getAttribute('role') === 'textbox';
                
                if (isInteractive) {
                    const text = (node.innerText || node.textContent || node.getAttribute('aria-label') || node.getAttribute('value') || '').trim();
                    const rect = node.getBoundingClientRect();
                    const style = window.getComputedStyle(node);
                    
                    const isVisible = style.display !== 'none' && 
                                     style.visibility !== 'hidden' && 
                                     style.opacity !== '0' &&
                                     rect.width > 0 && rect.height > 0;
                    
                    if ((text || node.tagName === 'INPUT' || node.getAttribute('contenteditable') === 'true') && isVisible) {
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
                            placeholder: node.getAttribute('placeholder') || node.getAttribute('data-placeholder') || '',
                            name: node.getAttribute('name') || '',
                            required: node.hasAttribute('required'),
                            disabled: node.disabled || false,
                            href: node.getAttribute('href') || '',
                            ariaLabel: node.getAttribute('aria-label') || '',
                            contentEditable: node.getAttribute('contenteditable') === 'true',
                            role: node.getAttribute('role') || ''
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
        
        automation_id = el_data['automationId']
        if automation_id in processed_ids:
            continue
        processed_ids.add(automation_id)
        
        is_contenteditable = el_data.get('contentEditable', False) or el_data.get('role') == 'textbox'
        
        _elements_cache[idx] = {
            'automationId': automation_id,
            'iframe': None,
            'text': el_data['text'],
            'isContentEditable': is_contenteditable
        }
        
        side = "RIGHT" if x > center_threshold else "LEFT"
        
        if is_contenteditable:
            hint = el_data.get('placeholder') or el_data.get('ariaLabel') or ''
            if hint:
                extra = f"COMPOSE_BOX placeholder='{hint[:40]}'"
            else:
                extra = "COMPOSE_BOX"
            display_text = el_data['text'][:30] if el_data['text'] else "(empty)"
        else:
            extra = format_shadow_context(el_data)
            display_text = el_data['text']
        
        state_parts.append(f"[{idx}] ({side}) {extra}: {display_text}")
        idx += 1
    
    # ===== PAGE SUMMARY =====
    if not state_parts:
        return "No elements"
    
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
        
        elif tag == 'select':
            required = ' (REQUIRED)' if element.get_attribute('required') else ''
            return f"SELECT{required}"
        
        elif tag == 'textarea':
            placeholder = element.get_attribute('placeholder') or ''
            required = ' (REQUIRED)' if element.get_attribute('required') else ''
            desc = f"TEXTAREA{required}"
            if placeholder:
                desc += f" placeholder='{placeholder[:30]}'"
            return desc
        
        elif tag == 'label':
            for_attr = element.get_attribute('for') or ''
            if for_attr:
                return f"LABEL[for='{for_attr[:20]}']"
            return "LABEL"
            
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
    
    elif tag == 'SELECT':
        required = ' (REQUIRED)' if el_data.get('required') else ''
        return f"SELECT{required}"
    
    elif tag == 'TEXTAREA':
        placeholder = el_data.get('placeholder', '')
        required = ' (REQUIRED)' if el_data.get('required') else ''
        desc = f"TEXTAREA{required}"
        if placeholder:
            desc += f" placeholder='{placeholder[:30]}'"
        return desc
    
    return tag