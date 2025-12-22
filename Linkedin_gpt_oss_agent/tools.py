import asyncio
import json
import random
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

PROMPT = "Find 'software engineer' jobs in florida and click on the first listing."

# --- PROMPTS ---

SYSTEM_PROMPT = """You are a LinkedIn job application automation agent.

PAGE TYPE DETECTION:
- If you see "[APPLY] ⭐⭐⭐" buttons → You are on JOB DETAILS page
- If you see many job listings → You are on JOBS LIST page
- If you see input fields + "Next" → You are on APPLICATION FORM page

WORKFLOW:
1. JOBS LIST page → Click a job listing to view details
2. JOB DETAILS page → Click the "[APPLY] ⭐⭐⭐" button (usually index 19-25)
3. APPLICATION FORM → Fill inputs, click "Next" or "Submit"

CRITICAL RULES:
- On JOB DETAILS page: ONLY click buttons with "[APPLY] ⭐⭐⭐"
- Do NOT click job listing links when you're already viewing that job
- If you clicked something and nothing changed, try a DIFFERENT index
- Job listing links are in [iframe0], Apply buttons are also in [iframe0]
"""

# --- BROWSER TOOLS SCHEMA ---

BROWSER_TOOLS = [
    {"type": "function", "function": {"name": "click", "description": "Click element by index", "parameters": {"type": "object", "properties": {"index": {"type": "integer"}}, "required": ["index"]}}},
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



# async def type_text(index, text):
#     if index not in _elements_cache:
#         return f"Invalid index {index}"
    
#     element_info = _elements_cache[index]
#     automation_id = element_info['automationId']
#     iframe_idx = element_info.get('iframe')
    
#     try:
#         # Switch to iframe if needed
#         if iframe_idx is not None:
#             iframes = _driver.find_elements(By.TAG_NAME, "iframe")
#             _driver.switch_to.frame(iframes[iframe_idx])
        
#         # Find the element
#         element = _driver.execute_script(f"""
#             return document.querySelector('[data-automation-id="{automation_id}"]');
#         """)
        
#         if not element:
#             _driver.switch_to.default_content()
#             return f"Element not found for index {index}"
        
#         # Click to focus
#         _driver.execute_script("arguments[0].click(); arguments[0].focus();", element)
#         await asyncio.sleep(0.5)
        
#         # Clear existing text
#         _driver.execute_script("arguments[0].value = '';", element)
        
#         # Type character by character with human-like delays
#         for char in text:
#             element.send_keys(char)
#             await asyncio.sleep(random.uniform(0.02, 0.08))
        
#         # Press Enter
#         element.send_keys(Keys.ENTER)
        
#         # Switch back to main frame
#         _driver.switch_to.default_content()
        
#         await asyncio.sleep(2)
#         return f"Typed '{text}' into index {index}"
        
#     except Exception as e:
#         _driver.switch_to.default_content()
#         return f"Type error: {str(e)[:100]}"

# async def press_key(key: str) -> str:
#     global driver
    
#     try:
#         # Find the active/focused element and send key to it
#         active = driver.switch_to.active_element
        
#         key_map = {
#             "enter": Keys.ENTER,
#             "tab": Keys.TAB,
#             "escape": Keys.ESCAPE,
#             "backspace": Keys.BACKSPACE,
#             "down": Keys.ARROW_DOWN,
#             "up": Keys.ARROW_UP,
#         }
        
#         active.send_keys(key_map.get(key.lower(), key))
#         time.sleep(0.3)
#         return f"✓ Pressed {key}"
#     except Exception as e:
#         return f"✗ Failed: {str(e)}"































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
        viewport_width = _driver.execute_script("return window.innerWidth;")
        center_threshold = viewport_width * 0.5
    except:
        center_threshold = 960
    
    iframes = _driver.find_elements(By.TAG_NAME, "iframe")
    print(f"Found {len(iframes)} iframes")
    
    state_parts = []
    idx = 0
    
    # ===== MAIN FRAME =====
    for tag in ['button', 'a', 'input']:
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
                
                extra = get_element_context(element, tag)
                
                _elements_cache[idx] = {
                    'automationId': automation_id,
                    'iframe': None,
                    'text': text[:60]
                }
                
                loc = element.location
                x = loc['x'] + element.size['width'] // 2
                side = "RIGHT" if x > center_threshold else "LEFT"
                
                is_apply = 'apply' in text.lower()
                marker = " [APPLY] ⭐⭐⭐" if is_apply else ""
                
                state_parts.append(f"[{idx}] ({side}) {extra}: {text[:60]}{marker}")
                idx += 1
            except:
                continue
    
    # ===== IFRAMES =====
    for iframe_idx, iframe in enumerate(iframes):
        try:
            _driver.switch_to.frame(iframe)
            
            for tag in ['button', 'a', 'input']:
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
                        
                        extra = get_element_context(element, tag)
                        
                        _elements_cache[idx] = {
                            'automationId': automation_id,
                            'iframe': iframe_idx,
                            'text': text[:60]
                        }
                        
                        loc = element.location
                        x = loc['x'] + element.size['width'] // 2
                        side = "RIGHT" if x > center_threshold else "LEFT"
                        
                        is_apply = 'apply' in text.lower()
                        marker = " [APPLY] ⭐⭐⭐" if is_apply else ""
                        
                        state_parts.append(f"[{idx}] ({side}) {extra}: {text[:60]} [iframe{iframe_idx}]{marker}")
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
        
        is_apply = 'apply' in el_data['text'].lower()
        marker = " [APPLY] ⭐⭐⭐" if is_apply else ""
        
        state_parts.append(f"[{idx}] ({side}) {extra}: {el_data['text']} [shadow]{marker}")
        idx += 1
    
    # ===== COUNT ELEMENT TYPES =====
    if not state_parts:
        return "No elements"
    
    apply_count = len([e for e in state_parts if '[APPLY]' in e])
    input_count = len([e for e in state_parts if 'INPUT' in e])
    button_count = len([e for e in state_parts if 'BUTTON' in e])
    link_count = len([e for e in state_parts if 'LINK' in e])
    next_count = len([e for e in state_parts if 'next' in e.lower()])
    submit_count = len([e for e in state_parts if 'submit' in e.lower()])
    review_count = len([e for e in state_parts if 'review' in e.lower()])
    
    # ===== DETECT PAGE TYPE AND FILTER =====
    if apply_count > 0 and input_count < 5:
        # JOB DETAILS PAGE - Show only actionable buttons
        page_type = "JOB_DETAILS"
        instruction = "You are viewing a job. Click the '[APPLY] ⭐⭐⭐' button to start application."
        
        filtered_parts = []
        for part in state_parts:
            # Keep Apply buttons (highest priority)
            if '[APPLY]' in part:
                filtered_parts.append(part)
            # Keep action buttons
            elif 'BUTTON' in part and any(kw in part.lower() for kw in ['apply', 'save', 'message', 'follow', 'share', 'tailor', 'help me stand out']):
                filtered_parts.append(part)
            # Keep any inputs (for filtering jobs)
            elif 'INPUT' in part:
                filtered_parts.append(part)
        
        state_parts = filtered_parts if filtered_parts else state_parts
    
    elif apply_count == 0 and button_count > 50 and link_count > 30:
        # JOBS LIST PAGE - Show job listings and navigation
        page_type = "JOBS_LIST"
        instruction = "You are on the jobs list. Click a job listing LINK to view details."
        
        filtered_parts = []
        for part in state_parts:
            # Keep job listing links (contain job titles)
            if 'LINK' in part and any(kw in part.lower() for kw in ['software', 'engineer', 'developer', 'analyst', 'manager', 'designer', 'verified job']):
                filtered_parts.append(part)
            # Keep Jobs navigation link
            elif 'Jobs' in part and 'LINK' in part:
                filtered_parts.append(part)
            # Keep search input
            elif 'INPUT' in part and ('search' in part.lower() or 'job' in part.lower()):
                filtered_parts.append(part)
        
        state_parts = filtered_parts if filtered_parts else state_parts
    
    elif input_count >= 5 or next_count > 0 or submit_count > 0 or review_count > 0:
        # APPLICATION FORM PAGE - Show inputs and form buttons
        page_type = "APPLICATION_FORM"
        instruction = "You are on an application form. Fill required inputs and click 'Next' or 'Submit'."
        
        filtered_parts = []
        for part in state_parts:
            # Keep all inputs
            if 'INPUT' in part:
                filtered_parts.append(part)
            # Keep form navigation buttons
            elif 'BUTTON' in part and any(kw in part.lower() for kw in ['next', 'submit', 'review', 'back', 'continue', 'send', 'upload']):
                filtered_parts.append(part)
            # Keep Apply buttons if still present
            elif '[APPLY]' in part:
                filtered_parts.append(part)
        
        state_parts = filtered_parts if filtered_parts else state_parts
    
    elif apply_count == 0 and button_count > 80:
        # FEED/HOME PAGE - Show only main navigation
        page_type = "FEED"
        instruction = "You are on LinkedIn feed. Click 'Jobs' link to go to jobs section."
        
        filtered_parts = []
        for part in state_parts:
            # Keep main navigation links
            if 'LINK' in part and any(kw in part for kw in ['Jobs', 'Home', 'My Network', 'Messaging']):
                filtered_parts.append(part)
            # Keep search
            elif 'INPUT' in part and 'search' in part.lower():
                filtered_parts.append(part)
        
        state_parts = filtered_parts if filtered_parts else state_parts
    
    else:
        # UNKNOWN PAGE - Show everything
        page_type = "UNKNOWN"
        instruction = "Analyze the page and determine next action."
    
    # ===== BUILD FINAL OUTPUT =====
    summary = f"""PAGE TYPE: {page_type}
INSTRUCTION: {instruction}

PAGE SUMMARY:
- Easy Apply buttons: {apply_count}
- Total buttons: {button_count}
- Input fields: {input_count}
- Links: {link_count}
- Next buttons: {next_count}
- Submit buttons: {submit_count}
- Review buttons: {review_count}
- Showing {len(state_parts)} most relevant elements (out of {idx} total)

ELEMENTS:
"""
    
    return summary + "\n".join(state_parts)


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
    
