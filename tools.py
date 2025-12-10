import time
import pyperclip
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
import platform
import os

driver = None
elements_cache = []

async def open_browser() -> str:
    global driver
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    options.add_argument('--window-position=-2000,0')
    options.add_argument('--window-size=1920,1080')
    profile_path = os.path.expanduser('~/AI Studio/chrome_automation_profile')
    driver = uc.Chrome(options=options, version_main=142, user_data_dir=profile_path)


async def open_url(url: str) -> str:
    global driver
    driver.get(url)


async def go_back() -> str:
    """Navigate back in browser history"""
    global driver
    
    try:
        driver.back()
        time.sleep(1)
        return "✓ Navigated back"
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def handle_alert(action: str = "accept") -> str:
    """Handle JS alert: 'accept' or 'dismiss'"""
    global driver
    
    try:
        alert = driver.switch_to.alert
        text = alert.text
        if action == "accept":
            alert.accept()
        else:
            alert.dismiss()
        return f"✓ Alert {action}ed: {text}"
    except Exception as e:
        return f"✗ No alert or failed: {str(e)}"


async def scroll(direction: str = "down", amount: int = 500) -> str:
    global driver
    
    try:
        if direction == "down":
            driver.execute_script(f"window.scrollBy(0, {amount});")
        elif direction == "up":
            driver.execute_script(f"window.scrollBy(0, -{amount});")
        elif direction == "top":
            driver.execute_script("window.scrollTo(0, 0);")
        elif direction == "bottom":
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        time.sleep(0.3)
        return f"✓ Scrolled {direction}"
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def type_text(element_index: int, text: str, clear_first: bool = True) -> str:
    global driver, elements_cache
    
    try:
        element = elements_cache[element_index]
        
        contenteditable = element.get_attribute("contenteditable")
        is_contenteditable = contenteditable == "true"
        
        # Detect Mac vs Windows/Linux
        is_mac = platform.system() == "Darwin"
        modifier_key = Keys.COMMAND if is_mac else Keys.CONTROL
        # print(f"  DEBUG: is_mac={is_mac}, using {'CMD' if is_mac else 'CTRL'}")
        
        if is_contenteditable:
            print("  DEBUG: Using clipboard paste method")
            
            element.click()
            time.sleep(0.3)
            
            if clear_first:
                ActionChains(driver).key_down(modifier_key).send_keys('a').key_up(modifier_key).perform()
                ActionChains(driver).send_keys(Keys.DELETE).perform()
                time.sleep(0.2)
            
            # Paste from clipboard
            print("hello")
            pyperclip.copy(text)
            print(f"  DEBUG: Copied to clipboard: {pyperclip.paste()}")
            
            ActionChains(driver).key_down(modifier_key).send_keys('v').key_up(modifier_key).perform()
            time.sleep(0.3)
            print("  DEBUG: Pressed CMD+V")
            
        else:
            if clear_first:
                element.clear()
            element.send_keys(text)
        
        return f"✓ Typed '{text}' into element {element_index}"
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"✗ Failed: {str(e)}"






async def upload_file_auto(file_path: str) -> str:
    """
    Upload file on any website. Finds hidden file inputs automatically.
    
    file_path can be:
    - Just filename: "resume.pdf" → searches common folders
    - Relative path: "docs/resume.pdf" 
    - Absolute path: "/Users/john/resume.pdf"
    - Home path: "~/Documents/resume.pdf"
    """
    global driver
    import os
    
    original_input = file_path
    
    # Expand home directory (~)
    file_path = os.path.expanduser(file_path)
    
    # If not absolute, search common locations
    if not os.path.isabs(file_path):
        search_locations = [
            os.getcwd(),                           # Current directory
            os.path.expanduser('~/Documents'),     # Documents
            os.path.expanduser('~/Downloads'),     # Downloads
            os.path.expanduser('~/Desktop'),       # Desktop
            os.path.expanduser('~'),               # Home folder
        ]
        
        found = False
        for base in search_locations:
            full_path = os.path.join(base, file_path)
            if os.path.exists(full_path):
                file_path = full_path
                found = True
                break
        
        if not found:
            # List what we searched
            return f"✗ File '{original_input}' not found. Searched: Documents, Downloads, Desktop, Home"
    
    # Final check
    if not os.path.exists(file_path):
        return f"✗ File not found: {file_path}"
    
    try:
        # Find ANY file input on the page (works for any website)
        file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        
        if not file_inputs:
            return "✗ No file upload element found on page"
        
        # Use the first available file input
        file_input = file_inputs[0]
        file_input.send_keys(file_path)
        time.sleep(1)
        
        return f"✓ File uploaded: {os.path.basename(file_path)} (from {file_path})"
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"




















































































# display saga


async def get_page_state(include_text=False, verbosity="normal"):
    """Enhanced to capture popup/modal content"""
    global elements_cache  # ← Add this
    
    script = """
    const elements = [];
    
    // Scan multiple DOM layers
    const layers = [
        document.body,  // Main content
        ...document.querySelectorAll('[role="dialog"]'),  // Modals
        ...document.querySelectorAll('[role="menu"]'),  // Dropdowns
        ...document.querySelectorAll('.popup, .modal, .overlay, [class*="popup"], [class*="modal"]'),
        ...document.querySelectorAll('[aria-modal="true"]'),
        ...document.querySelectorAll('[data-testid*="menu"], [data-testid*="modal"]')
    ];
    
    // Get all interactive elements from ALL layers
    layers.forEach(layer => {
        if (!layer) return;
        
        const interactive = layer.querySelectorAll(
            'button, a, input, textarea, [role="button"], [contenteditable], ' +
            '[onclick], select, [role="menuitem"], [role="option"]'
        );
        
        interactive.forEach(el => {
            // Check if element is actually visible
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            
            if (rect.width > 0 && rect.height > 0 && 
                style.display !== 'none' && 
                style.visibility !== 'hidden' &&
                style.opacity !== '0') {
                
                // Store actual element reference
                elements.push(el);
            }
        });
    });
    
    return elements;
    """
    
    # Get actual element references
    raw_elements = driver.execute_script(script)
    
    # Update global cache with actual WebElement objects
    elements_cache = raw_elements
    
    # Now extract info for display
    element_info = []
    for idx, el in enumerate(raw_elements):
        try:
            info = driver.execute_script("""
                const el = arguments[0];
                const style = window.getComputedStyle(el);
                const layer = el.closest('[role="dialog"], [role="menu"], [aria-modal="true"]') || document.body;
                
                return {
                    index: arguments[1],
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent.trim().slice(0, 100),
                    type: el.type || el.getAttribute('role') || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    dataIcon: el.getAttribute('data-icon') || '',
                    classes: el.className,
                    isInPopup: layer !== document.body,
                    zIndex: style.zIndex
                };
            """, el, idx)
            element_info.append(info)
        except:
            continue
    
    # Helper function to format element info
    def format_element(el):
        parts = [f"[{el['index']}]"]
        
        if el.get('tag'):
            parts.append(el['tag'])
        
        if el.get('type'):
            parts.append(f"type={el['type']}")
        
        # Show if it's in a popup
        if el.get('isInPopup'):
            parts.append("🔴POPUP")
        
        # WhatsApp data-icon
        if el.get('dataIcon'):
            parts.append(f"icon={el['dataIcon']}")
        
        # Aria label
        if el.get('ariaLabel'):
            parts.append(f"aria={el['ariaLabel'][:50]}")
        
        # Text content
        if el.get('text'):
            parts.append(f"'{el['text'][:60]}'")
        
        return " ".join(parts)
    
    # Format output highlighting popup elements
    output = [f"URL: {driver.current_url}", f"Title: {driver.title}", ""]
    
    popup_elements = [e for e in element_info if e.get('isInPopup')]
    if popup_elements:
        output.append("=== POPUP/MODAL ELEMENTS (PRIORITY) ===")
        for el in popup_elements[:20]:
            output.append(format_element(el))
        output.append("")
    
    output.append("=== PAGE ELEMENTS ===")
    for el in [e for e in element_info if not e.get('isInPopup')][:30]:
        output.append(format_element(el))
    
    if include_text:
        output.append("\n=== PAGE TEXT ===")
        output.append(driver.execute_script("return document.body.innerText;")[:2000])
    
    return "\n".join(output)

async def find_elements_by_text(text: str, element_type: str = None) -> str:
    """
    Universal text search - works on any website.
    
    element_type: Optional filter like 'button', 'link', 'listitem', 'input'
    """
    global driver, elements_cache
    
    try:
        # Case-insensitive XPath search
        xpath = f"//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
        elements = driver.find_elements(By.XPATH, xpath)
        
        # Also search aria-labels
        aria_xpath = f"//*[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
        elements.extend(driver.find_elements(By.XPATH, aria_xpath))
        
        # Filter by element type if specified
        if element_type:
            type_map = {
                'button': lambda e: e.tag_name == 'button' or e.get_attribute('role') == 'button',
                'link': lambda e: e.tag_name == 'a' or e.get_attribute('role') == 'link',
                'input': lambda e: e.tag_name == 'input' or e.get_attribute('role') == 'textbox',
                'listitem': lambda e: e.get_attribute('role') == 'listitem',
            }
            filter_fn = type_map.get(element_type.lower())
            if filter_fn:
                elements = [e for e in elements if filter_fn(e)]
        
        # Collect visible, unique elements + their clickable parents
        candidates = []
        seen = set()
        
        for el in elements:
            if not el.is_displayed():
                continue
            
            # Add element itself
            try:
                el_id = id(el)
                if el_id not in seen:
                    candidates.append(el)
                    seen.add(el_id)
                
                # Check if parent is more clickable (common pattern)
                parent = el.find_element(By.XPATH, "..")
                parent_role = parent.get_attribute("role")
                parent_onclick = parent.get_attribute("onclick")
                
                # Add parent if it's interactive
                if parent_role in ['button', 'link', 'listitem', 'menuitem', 'tab'] or parent_onclick:
                    parent_id = id(parent)
                    if parent_id not in seen:
                        candidates.append(parent)
                        seen.add(parent_id)
            except:
                pass
        
        if not candidates:
            return f"✗ No visible elements found with text '{text}'"
        
        # Add to cache and return results
        result_lines = [f"Found {len(candidates)} elements with '{text}':"]
        
        new_indices = []
        for element in candidates[:10]:  # Limit to 10
            try:
                idx = len(elements_cache)
                elements_cache.append(element)
                new_indices.append(idx)
                
                tag = element.tag_name
                role = element.get_attribute("role") or ""
                el_text = (element.text or "")[:60].strip()
                aria = (element.get_attribute("aria-label") or "")[:60]
                
                desc = f"  [{idx}] <{tag}"
                if role:
                    desc += f" role={role}"
                desc += ">"
                
                if el_text:
                    desc += f' "{el_text}"'
                elif aria:
                    desc += f' aria="{aria}"'
                
                result_lines.append(desc)
            except:
                continue
        
        if new_indices:
            result_lines.append(f"\n✓ You can now click these using indices: {new_indices}")
        
        return "\n".join(result_lines)
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"



































































































































































# click saga

async def click(element_index: int) -> str:
    global driver, elements_cache
    
    try:
        element = elements_cache[element_index]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.2)
        element.click()
        time.sleep(0.5)
        return f"✓ Clicked element {element_index}"
    
    except StaleElementReferenceException:
        return f"✗ Element {element_index} is stale - call get_page_state() to refresh"
    except Exception as e:
        return f"✗ Failed: {str(e)}"

async def js_click(element_index: int) -> str:
    global driver, elements_cache
    
    try:
        element = elements_cache[element_index]
        driver.execute_script("arguments[0].click();", element)
        time.sleep(0.5)
        return f"✓ JS clicked element {element_index}"
    except Exception as e:
        return f"✗ Failed: {str(e)}"

async def click_element_with_text(text: str) -> str:
    """Universal click-by-text - tries multiple strategies"""
    global driver
    
    try:
        # Strategy 1: Direct text match
        xpath = f"//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
        elements = driver.find_elements(By.XPATH, xpath)
        
        # Strategy 2: Aria-label match
        aria_xpath = f"//*[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
        elements.extend(driver.find_elements(By.XPATH, aria_xpath))
        
        # Try clicking visible elements
        for element in elements:
            if not element.is_displayed():
                continue
            
            # Try 1: Regular click
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.2)
                element.click()
                time.sleep(0.5)
                return f"✓ Clicked element with text '{text}'"
            except:
                pass
            
            # Try 2: JS click
            try:
                driver.execute_script("arguments[0].click();", element)
                time.sleep(0.5)
                return f"✓ JS clicked element with text '{text}'"
            except:
                pass
            
            # Try 3: Parent click (for nested structures)
            try:
                parent = element.find_element(By.XPATH, "..")
                parent.click()
                time.sleep(0.5)
                return f"✓ Clicked parent of element with text '{text}'"
            except:
                pass
        
        return f"✗ Found {len(elements)} elements with '{text}' but none were clickable"
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"


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


async def hover(element_index: int) -> str:
    """Hover over element to trigger dropdowns/tooltips"""
    global driver, elements_cache
    
    try:
        element = elements_cache[element_index]
        ActionChains(driver).move_to_element(element).perform()
        time.sleep(0.3)
        return f"✓ Hovered element {element_index}"
    except Exception as e:
        return f"✗ Failed: {str(e)}"
