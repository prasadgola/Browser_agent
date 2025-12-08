import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
import time
import pyperclip
from selenium.webdriver.common.keys import Keys
import platform

driver = None
elements_cache = []

async def open_browser() -> str:
    global driver
    
    try:
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--start-maximized')
        
        driver = uc.Chrome(options=options, version_main=142)

        
        return "✓ Browser opened"
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def open_url(url: str) -> str:
    global driver
    
    try:
        driver.get(url)
        time.sleep(1)
        return f"✓ Navigated to: {url}"
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"


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


async def type_text(element_index: int, text: str, clear_first: bool = True) -> str:
    global driver, elements_cache
    
    try:
        element = elements_cache[element_index]
        
        contenteditable = element.get_attribute("contenteditable")
        is_contenteditable = contenteditable == "true"
        
        # Detect Mac vs Windows/Linux
        is_mac = platform.system() == "Darwin"
        modifier_key = Keys.COMMAND if is_mac else Keys.CONTROL
        print(f"  DEBUG: is_mac={is_mac}, using {'CMD' if is_mac else 'CTRL'}")
        
        if is_contenteditable:
            print("  DEBUG: Using clipboard paste method")
            
            element.click()
            time.sleep(0.3)
            
            if clear_first:
                ActionChains(driver).key_down(modifier_key).send_keys('a').key_up(modifier_key).perform()
                ActionChains(driver).send_keys(Keys.DELETE).perform()
                time.sleep(0.2)
            
            # Paste from clipboard
            import pyperclip
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




# tools.py - Universal get_page_state()

async def get_page_state(include_text: bool = False, verbosity: str = "normal") -> str:
    print("get_page_state")
    time.sleep(2)
    """
    Extract page state that works for ANY website.
    
    verbosity: 
    - "minimal": Just basic interactive elements
    - "normal": Standard info (default)
    - "detailed": Rich context for complex apps
    """
    global driver, elements_cache
    
    try:
        new_cache = []
        
        # Universal selectors that work everywhere
        selectors = [
            # Standard HTML
            "a[href]", "button", "input", "textarea", "select",
            
            # Modern web apps (ARIA roles)
            "[role='button']", "[role='link']", "[role='textbox']",
            "[role='listitem']", "[role='menuitem']", "[role='tab']",
            "[role='checkbox']", "[role='radio']", "[role='row']",
            
            # Interactive patterns
            "[onclick]", "[tabindex='0']", "[tabindex='-1']",
            "[contenteditable='true']",
            
            # Special elements
            "iframe", "input[type='file']",
        ]
        
        all_elements = driver.find_elements(By.CSS_SELECTOR, ", ".join(selectors))
        
        state_lines = [
            f"Page: {driver.title}",
            f"URL: {driver.current_url}",
            ""
        ]
        
        # Detect page type to adjust detail level
        url = driver.current_url.lower()
        is_complex_app = any(domain in url for domain in [
            'whatsapp', 'slack', 'discord', 'notion', 'figma', 
            'gmail', 'outlook', 'teams', 'zoom'
        ])
        
        # Auto-adjust verbosity for complex apps
        if is_complex_app and verbosity == "normal":
            verbosity = "detailed"
            state_lines.append("ℹ️ Complex web app detected - using detailed mode")
            state_lines.append("")
        
        state_lines.append("Interactive elements:")
        
        for element in all_elements:
            try:
                if not element.is_displayed():
                    continue
                
                # === BASIC INFO (always collected) ===
                tag = element.tag_name
                text = (element.text or "").strip()[:100]
                role = element.get_attribute("role") or ""
                aria_label = element.get_attribute("aria-label") or ""
                el_type = element.get_attribute("type") or ""
                placeholder = element.get_attribute("placeholder") or ""
                name = element.get_attribute("name") or ""
                title = element.get_attribute("title") or ""
                value = element.get_attribute("value") or ""
                
                idx = len(new_cache)
                
                # === BUILD DESCRIPTION ===
                if verbosity == "minimal":
                    # Just tag, role, and main identifier
                    desc = f"[{idx}] <{tag}>"
                    if role:
                        desc += f" role='{role}'"
                    if text:
                        desc += f" '{text[:50]}'"
                    elif aria_label:
                        desc += f" '{aria_label[:50]}'"
                
                elif verbosity == "detailed":
                    # Rich context for complex apps
                    desc_parts = [f"[{idx}]"]
                    
                    # Tag + role
                    if role:
                        desc_parts.append(f"<{tag} role={role}>")
                    else:
                        desc_parts.append(f"<{tag}>")
                    
                    # Type
                    if el_type:
                        desc_parts.append(f"type={el_type}")
                    
                    # Main text/label (most important!)
                    main_identifier = text or aria_label or placeholder or title or value or name
                    if main_identifier:
                        desc_parts.append(f'"{main_identifier[:80]}"')
                    
                    # Parent context if element has no clear text
                    if not text and verbosity == "detailed":
                        try:
                            parent = element.find_element(By.XPATH, "..")
                            parent_role = parent.get_attribute("role")
                            parent_text = parent.text.strip()[:50] if parent.text else ""
                            
                            if parent_role and parent_role != role:
                                desc_parts.append(f"(in {parent_role})")
                            elif parent_text and parent_text != text:
                                desc_parts.append(f"(in '{parent_text}')")
                        except:
                            pass
                    
                    # Get nested text if element is empty
                    if not text and len(desc_parts) <= 3:
                        try:
                            children = element.find_elements(By.XPATH, ".//*[text()]")
                            if children:
                                nested = " | ".join([c.text.strip()[:30] for c in children[:2] if c.text.strip()])
                                if nested:
                                    desc_parts.append(f"contains: {nested}")
                        except:
                            pass
                    
                    desc = " ".join(desc_parts)
                
                else:  # normal
                    # Balanced: clear but not overwhelming
                    desc = f"[{idx}] <{tag}"
                    if role:
                        desc += f" role={role}"
                    if el_type:
                        desc += f" type={el_type}"
                    desc += ">"
                    
                    # Best available identifier
                    identifier = text or aria_label or placeholder or title or name
                    if identifier:
                        desc += f' "{identifier[:60]}"'
                
                state_lines.append(desc)
                new_cache.append(element)
                
            except (StaleElementReferenceException, Exception):
                continue
        
        elements_cache = new_cache
        
        state_lines.append(f"\nTotal: {len(new_cache)} interactive elements")
        
        # Include page text if requested OR if very few elements found
        if include_text or len(new_cache) < 5:
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                lines = [l.strip() for l in body_text.split('\n') if l.strip() and len(l.strip()) > 2]
                
                # Remove duplicates (common in SPAs)
                unique_lines = []
                seen = set()
                for line in lines[:40]:
                    if line not in seen:
                        unique_lines.append(line)
                        seen.add(line)
                        if len(unique_lines) >= 25:
                            break
                
                if unique_lines:
                    state_lines.append("\n--- Visible Text ---")
                    state_lines.extend(unique_lines)
            except:
                pass
        
        return "\n".join(state_lines)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"✗ Failed: {str(e)}"

async def find_elements_by_text(text: str, element_type: str = None) -> str:
    print("find_elements_by_text")
    time.sleep(2)
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


async def click_element_with_text(text: str) -> str:
    print("click_element_with_text")
    time.sleep(2)   
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
    print("press_key")
    time.sleep(2)   
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
    print("hover")
    time.sleep(2)
    """Hover over element to trigger dropdowns/tooltips"""
    global driver, elements_cache
    
    try:
        element = elements_cache[element_index]
        ActionChains(driver).move_to_element(element).perform()
        time.sleep(0.3)
        return f"✓ Hovered element {element_index}"
    except Exception as e:
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


async def go_back() -> str:
    print("go_back")
    time.sleep(2)
    """Navigate back in browser history"""
    global driver
    
    try:
        driver.back()
        time.sleep(1)
        return "✓ Navigated back"
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def handle_alert(action: str = "accept") -> str:
    print("handle_alert")
    time.sleep(2)
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