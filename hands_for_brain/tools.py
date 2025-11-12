# tools.py
"""
Browser control tools for job application agent.
These are the agent's "hands" - mouse and keyboard controls.
"""

import json
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page

# ============================================
# GLOBAL BROWSER STATE
# ============================================
browser: Browser = None
page: Page = None
playwright_instance = None

# ============================================
# BROWSER MANAGEMENT
# ============================================

async def open_browser(url: str = "https://www.google.com") -> str:
    global browser, page, playwright_instance
    
    try:
        playwright_instance = await async_playwright().start()
        
        # Launch with more human-like settings
        browser = await playwright_instance.chromium.launch(
            headless=False,
            slow_mo=500,
            args=[
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        # Create context with realistic settings
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/Chicago'
        )
        
        page = await context.new_page()
        
        # Hide webdriver property (makes browser look non-automated)
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        await page.goto(url, wait_until="domcontentloaded")
        
        return f"✓ Browser opened at: {url}"
    
    except Exception as e:
        import traceback
        return f"✗ Failed: {str(e)}\n{traceback.format_exc()}"


async def close_browser() -> str:
    """
    Closes the browser and cleans up.
    This is like shutting down your computer and going to sleep.
    
    Returns:
        Success message
    """
    global browser, page, playwright_instance
    
    try:
        if page:
            await page.close()
        if browser:
            await browser.close()
        if playwright_instance:
            await playwright_instance.stop()
        
        page = None
        browser = None
        playwright_instance = None
        
        return "✓ Browser closed. Goodnight!"
    
    except Exception as e:
        return f"✗ Failed to close browser: {str(e)}"


# ============================================
# VISION (SCREEN DISPLAY)
# ============================================

async def screen_display() -> str:
    """
    Returns what's visible on the screen.
    Like looking at your monitor and seeing what's there.
    
    Returns:
        JSON string with page info, elements, and accessibility tree
    """
    global page
    
    if not page:
        return json.dumps({"error": "Browser not open. Call open_browser() first."})
    
    try:
        # Get basic page info
        title = await page.title()
        url = page.url
        viewport = page.viewport_size
        
        # Get accessibility tree (page structure)
        try:
            accessibility = await page.accessibility.snapshot()
        except:
            accessibility = None
        
        # Get all interactive elements with their positions
        elements = await page.evaluate("""
            () => {
                const interactable = document.querySelectorAll(
                    'button, a, input, textarea, select, [role="button"], [role="link"]'
                );
                
                return Array.from(interactable).map((el, index) => {
                    const rect = el.getBoundingClientRect();
                    
                    // Only return visible elements
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
                        x: Math.round(rect.x + rect.width / 2),  // Center point
                        y: Math.round(rect.y + rect.height / 2),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    };
                }).filter(el => el !== null);
            }
        """)
        
        # Build response
        display_data = {
            "title": title,
            "url": url,
            "viewport": viewport,
            "accessibility": accessibility,
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
    """
    Click the mouse at specific coordinates.
    Like physically clicking your mouse at a position on screen.
    
    Args:
        x: Horizontal position (pixels from left)
        y: Vertical position (pixels from top)
    
    Returns:
        Success/failure message
    """
    global page
    
    if not page:
        return "✗ Browser not open. Call open_browser() first."
    
    try:
        await page.mouse.click(x, y)
        return f"✓ Clicked at position ({x}, {y})"
    
    except Exception as e:
        return f"✗ Failed to click at ({x}, {y}): {str(e)}"


async def mouse_move(x: int, y: int) -> str:
    """
    Move the mouse to specific coordinates without clicking.
    Useful for triggering hover effects or menus.
    
    Args:
        x: Horizontal position (pixels from left)
        y: Vertical position (pixels from top)
    
    Returns:
        Success/failure message
    """
    global page
    
    if not page:
        return "✗ Browser not open. Call open_browser() first."
    
    try:
        await page.mouse.move(x, y)
        return f"✓ Moved mouse to ({x}, {y})"
    
    except Exception as e:
        return f"✗ Failed to move mouse to ({x}, {y}): {str(e)}"


async def mouse_right_click(x: int, y: int) -> str:
    """
    Right-click the mouse at specific coordinates.
    Opens context menus.
    
    Args:
        x: Horizontal position (pixels from left)
        y: Vertical position (pixels from top)
    
    Returns:
        Success/failure message
    """
    global page
    
    if not page:
        return "✗ Browser not open. Call open_browser() first."
    
    try:
        await page.mouse.click(x, y, button="right")
        return f"✓ Right-clicked at position ({x}, {y})"
    
    except Exception as e:
        return f"✗ Failed to right-click at ({x}, {y}): {str(e)}"


# ============================================
# KEYBOARD CONTROLS
# ============================================

async def keyboard_type(text: str) -> str:
    """
    Type text using the keyboard.
    Like physically typing on your keyboard.
    Make sure cursor is in the right field first (click on it).
    
    Args:
        text: Text to type
    
    Returns:
        Success/failure message
    """
    global page
    
    if not page:
        return "✗ Browser not open. Call open_browser() first."
    
    try:
        await page.keyboard.type(text, delay=50)  # 50ms between keystrokes (human-like)
        return f"✓ Typed: {text[:50]}{'...' if len(text) > 50 else ''}"
    
    except Exception as e:
        return f"✗ Failed to type text: {str(e)}"


# ============================================
# SCROLL CONTROL
# ============================================

async def scroll(direction: str = "down", amount: Optional[int] = None) -> str:
    """
    Scroll the page up or down.
    Like using your mouse wheel or trackpad.
    
    Args:
        direction: "up" or "down"
        amount: Pixels to scroll (optional, defaults to one viewport height)
    
    Returns:
        Success/failure message
    """
    global page
    
    if not page:
        return "✗ Browser not open. Call open_browser() first."
    
    try:
        if amount is None:
            # Default: scroll one full viewport
            amount = page.viewport_size['height']
        
        # Scroll up means negative amount
        if direction.lower() == "up":
            amount = -amount
        
        await page.evaluate(f"window.scrollBy(0, {amount})")
        
        return f"✓ Scrolled {direction} by {abs(amount)} pixels"
    
    except Exception as e:
        return f"✗ Failed to scroll: {str(e)}"