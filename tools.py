import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
import time

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
        if clear_first:
            element.clear()
        element.send_keys(text)
        return f"✓ Typed '{text}' into element {element_index}"
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def select_option(element_index: int, value: str = None, visible_text: str = None, index: int = None) -> str:
    global driver, elements_cache
    
    try:
        element = elements_cache[element_index]
        select = Select(element)
        
        if visible_text:
            select.select_by_visible_text(visible_text)
        elif value:
            select.select_by_value(value)
        elif index is not None:
            select.select_by_index(index)
        
        return f"✓ Selected option in element {element_index}"
    
    except Exception as e:
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


async def get_text(element_index: int) -> str:
    global driver, elements_cache
    
    try:
        element = elements_cache[element_index]
        text = element.text or element.get_attribute('value') or element.get_attribute('innerText')
        return f"✓ Text: {text}"
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def wait_for_element(selector: str, timeout: int = 10) -> str:
    global driver
    
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return f"✓ Element found: {selector}"
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def close_browser() -> str:
    global driver
    
    try:
        driver.quit()
        driver = None
        return "✓ Browser closed"
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def get_page_state(include_text: bool = False) -> str:
    """Extract page state for the model"""
    global driver, elements_cache
    
    try:
        new_cache = []  # Build separately
        
        selectors = [
            "a[href]",
            "button", 
            "input",
            "textarea",
            "select",
            "[role='button']",
            "[role='link']",
            "[role='checkbox']",
            "[role='radio']",
            "[onclick]",
            "[tabindex='0']",
            "iframe",
            "input[type='file']",
        ]
        
        all_elements = driver.find_elements(By.CSS_SELECTOR, ", ".join(selectors))
        
        state_lines = [
            f"Page: {driver.title}",
            f"URL: {driver.current_url}",
            f"Tabs open: {len(driver.window_handles)}",
            "",
            "Interactive elements:"
        ]
        
        for element in all_elements:
            try:
                if not element.is_displayed():
                    continue
                
                tag = element.tag_name
                text = (element.text or element.get_attribute("value") or "")[:50].strip()
                placeholder = element.get_attribute("placeholder") or ""
                el_type = element.get_attribute("type") or ""
                aria_label = element.get_attribute("aria-label") or ""
                name = element.get_attribute("name") or ""
                checked = element.get_attribute("checked")
                disabled = element.get_attribute("disabled")
                
                idx = len(new_cache)
                desc = f"[{idx}] <{tag}>"
                
                if el_type:
                    desc += f" type='{el_type}'"
                if disabled:
                    desc += " [DISABLED]"
                if checked:
                    desc += " [CHECKED]"
                if text:
                    desc += f" '{text}'"
                elif placeholder:
                    desc += f" placeholder='{placeholder}'"
                elif aria_label:
                    desc += f" aria='{aria_label}'"
                elif name:
                    desc += f" name='{name}'"
                
                state_lines.append(desc)
                new_cache.append(element)
                
            except StaleElementReferenceException:
                continue
        
        elements_cache = new_cache
        
        if include_text:
            body_text = driver.find_element(By.TAG_NAME, "body").text[:2000]
            state_lines.append("\n--- Page Text ---")
            state_lines.append(body_text)
        
        return "\n".join(state_lines)
    
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def press_key(key: str) -> str:
    """Press keyboard key: 'enter', 'tab', 'escape', 'backspace'"""
    from selenium.webdriver.common.keys import Keys
    global driver
    
    key_map = {
        "enter": Keys.ENTER,
        "tab": Keys.TAB,
        "escape": Keys.ESCAPE,
        "backspace": Keys.BACKSPACE,
        "down": Keys.ARROW_DOWN,
        "up": Keys.ARROW_UP,
    }
    
    try:
        driver.switch_to.active_element.send_keys(key_map.get(key.lower(), key))
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

async def switch_tab(tab_index: int = -1) -> str:
    """Switch to tab by index (-1 for last/newest tab)"""
    global driver
    
    try:
        handles = driver.window_handles
        driver.switch_to.window(handles[tab_index])
        time.sleep(0.5)
        return f"✓ Switched to tab {tab_index} ({len(handles)} total)"
    except Exception as e:
        return f"✗ Failed: {str(e)}"

async def close_tab() -> str:
    """Close current tab and switch to previous"""
    global driver
    
    try:
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])
        return "✓ Closed tab"
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def upload_file(element_index: int, file_path: str) -> str:
    """Upload file to input[type='file'] element"""
    global elements_cache
    
    try:
        element = elements_cache[element_index]
        element.send_keys(file_path)
        time.sleep(1)
        return f"✓ Uploaded {file_path}"
    except Exception as e:
        return f"✗ Failed: {str(e)}"


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


async def get_page_text() -> str:
    """Get all visible text on page (not just interactive elements)"""
    global driver
    
    try:
        text = driver.find_element(By.TAG_NAME, "body").text
        if len(text) > 4000:
            text = text[:4000] + "\n... [truncated]"
        return f"Page text:\n{text}"
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def switch_to_iframe(element_index: int = None) -> str:
    """Switch to iframe by index, or back to main if None"""
    global driver, elements_cache
    
    try:
        if element_index is None:
            driver.switch_to.default_content()
            return "✓ Switched to main content"
        else:
            iframe = elements_cache[element_index]
            driver.switch_to.frame(iframe)
            return f"✓ Switched to iframe {element_index}"
    except Exception as e:
        return f"✗ Failed: {str(e)}"


async def wait_for_page_load(timeout: int = 10) -> str:
    """Wait for page to fully load"""
    global driver
    
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return "✓ Page loaded"
    except Exception as e:
        return f"✗ Timeout: {str(e)}"