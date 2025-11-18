import json
from typing import Optional
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

# ============================================
# GLOBAL BROWSER STATE
# ============================================
driver: uc.Chrome = None

# ============================================
# BROWSER MANAGEMENT
# ============================================

async def open_browser(url: str = "https://www.google.com") -> str:
    global driver
    
    try:
        options = uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--start-maximized')
        
        driver = uc.Chrome(options=options, version_main=None)
        driver.get(url)
        time.sleep(2)
        
        return f"✓ Browser opened at: {url}"
    
    except Exception as e:
        import traceback
        return f"✗ Failed: {str(e)}\n{traceback.format_exc()}"


async def close_browser() -> str:
    global driver
    
    try:
        if driver:
            driver.quit()
            driver = None
        
        return "✓ Browser closed. Goodnight!"
    
    except Exception as e:
        return f"✗ Failed to close browser: {str(e)}"


# ============================================
# VISION (SCREEN DISPLAY)
# ============================================

async def screen_display() -> str:
    global driver
    
    if not driver:
        return json.dumps({"error": "Browser not open. Call open_browser() first."})
    
    try:
        title = driver.title
        url = driver.current_url
        viewport = {
            "width": driver.execute_script("return window.innerWidth"),
            "height": driver.execute_script("return window.innerHeight")
        }
        
        elements = driver.execute_script("""
            const interactable = document.querySelectorAll(
                'button, a, input, textarea, select, [role="button"], [role="link"]'
            );
            
            return Array.from(interactable).map((el, index) => {
                const rect = el.getBoundingClientRect();
                
                if (el.offsetParent === null || rect.width === 0 || rect.height === 0) {
                    return null;
                }
                
                return {
                    id: `elem_${index}`,
                    tag: el.tagName.toLowerCase(),
                    type: el.type || '',
                    text: (el.textContent || '').trim().substring(0, 100),
                    placeholder: el.placeholder || '',
                    value: el.value || '',
                    ariaLabel: el.ariaLabel || el.getAttribute('aria-label') || '',
                    name: el.name || '',
                    x: Math.round(rect.x + rect.width / 2),
                    y: Math.round(rect.y + rect.height / 2),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                };
            }).filter(el => el !== null);
        """)
        
        display_data = {
            "title": title,
            "url": url,
            "viewport": viewport,
            "elements": elements,
            "element_count": len(elements)
        }
        
        return json.dumps(display_data, indent=2)
    
    except Exception as e:
        return json.dumps({"error": f"Failed to get screen display: {str(e)}"})


# ============================================
# MOUSE CONTROLS
# ============================================

async def mouse_click(x: int, y: int) -> str:
    global driver
    
    if not driver:
        return "✗ Browser not open. Call open_browser() first."
    
    try:
        actions = ActionChains(driver)
        actions.move_by_offset(x - driver.execute_script("return window.pageXOffset"), 
                              y - driver.execute_script("return window.pageYOffset"))
        actions.click()
        actions.perform()
        
        actions.reset_actions()
        
        return f"✓ Clicked at position ({x}, {y})"
    
    except Exception as e:
        return f"✗ Failed to click at ({x}, {y}): {str(e)}"


async def mouse_move(x: int, y: int) -> str:
    global driver
    
    if not driver:
        return "✗ Browser not open. Call open_browser() first."
    
    try:
        actions = ActionChains(driver)
        actions.move_by_offset(x - driver.execute_script("return window.pageXOffset"), 
                              y - driver.execute_script("return window.pageYOffset"))
        actions.perform()
        
        actions.reset_actions()
        
        return f"✓ Moved mouse to ({x}, {y})"
    
    except Exception as e:
        return f"✗ Failed to move mouse to ({x}, {y}): {str(e)}"


async def mouse_right_click(x: int, y: int) -> str:
    global driver
    
    if not driver:
        return "✗ Browser not open. Call open_browser() first."
    
    try:
        actions = ActionChains(driver)
        actions.move_by_offset(x - driver.execute_script("return window.pageXOffset"), 
                              y - driver.execute_script("return window.pageYOffset"))
        actions.context_click()
        actions.perform()
        
        actions.reset_actions()
        
        return f"✓ Right-clicked at position ({x}, {y})"
    
    except Exception as e:
        return f"✗ Failed to right-click at ({x}, {y}): {str(e)}"


# ============================================
# KEYBOARD CONTROLS
# ============================================

async def keyboard_type(text: str) -> str:
    global driver
    
    if not driver:
        return "✗ Browser not open. Call open_browser() first."
    
    try:
        actions = ActionChains(driver)
        for char in text:
            actions.send_keys(char)
            actions.pause(0.05)
        actions.perform()
        
        return f"✓ Typed: {text[:50]}{'...' if len(text) > 50 else ''}"
    
    except Exception as e:
        return f"✗ Failed to type text: {str(e)}"


# ============================================
# SCROLL CONTROL
# ============================================

async def scroll(direction: str = "down", amount: Optional[int] = None) -> str:
    global driver
    
    if not driver:
        return "✗ Browser not open. Call open_browser() first."
    
    try:
        if amount is None:
            amount = driver.execute_script("return window.innerHeight")
        
        if direction.lower() == "up":
            amount = -amount
        
        driver.execute_script(f"window.scrollBy(0, {amount})")
        
        return f"✓ Scrolled {direction} by {abs(amount)} pixels"
    
    except Exception as e:
        return f"✗ Failed to scroll: {str(e)}"