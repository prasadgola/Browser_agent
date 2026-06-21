"""
gemma4_search_agent.py

Pure-vision browser agent. Loop:
  screenshot -> gemma4:31b (with tools) -> tool call -> execute on real Chrome -> repeat

The model only sees pixels. It decides what to click/type; the tools below are the
"hands" that perform it. Gemma returns boxes normalized to 0..1000, so every click
is converted to CSS pixels before hitting elementFromPoint.

Task: search Google for a randomly chosen query.
"""

import io
import json
import time
import base64
import random
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from PIL import Image

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gemma4:31b"
CHROME_MAIN = 149          # match installed Chrome
NORM = 1000.0              # gemma4 coordinate space
MAX_ACTIONS = 8
SEND_MAX_W = 1280          # downscale the image we send (normalized coords are
                           # resolution-independent, so this is free speed)

driver = None

QUERIES = [
    "why do cats purr",
    "best ramen in osaka",
    "how tall is mount kilimanjaro",
    "history of the typewriter",
    "what is a tardigrade",
    "longest river in south america",
]

# --------------------------------------------------------------------------- #
# browser setup
# --------------------------------------------------------------------------- #
def open_browser():
    global driver
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options, version_main=CHROME_MAIN)


def take_screenshot_b64():
    """Full-res screenshot for clicking truth; downscaled copy for the model."""
    png = driver.get_screenshot_as_png()
    img = Image.open(io.BytesIO(png)).convert("RGB")
    if img.width > SEND_MAX_W:
        ratio = SEND_MAX_W / img.width
        img = img.resize((SEND_MAX_W, int(img.height * ratio)))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# --------------------------------------------------------------------------- #
# TOOLS  (the actuators the model calls)
# --------------------------------------------------------------------------- #
def _flash(cx, cy):
    """Quick visual marker so you can watch where it clicks."""
    driver.execute_script("""
        var d = document.createElement('div');
        d.style.cssText = `position:fixed;left:${arguments[0]-12}px;top:${arguments[1]-12}px;
            width:24px;height:24px;border:3px solid red;border-radius:50%;
            z-index:2147483647;pointer-events:none;box-shadow:0 0 8px red;`;
        document.body.appendChild(d);
        setTimeout(()=>d.remove(), 1200);
    """, cx, cy)


def mouse_click(x, y):
    """x, y are [x1,x2] / [y1,y2] boxes in gemma's 0..1000 space. Click box center."""
    vp = driver.execute_script("return {w: window.innerWidth, h: window.innerHeight}")
    cx = int((x[0] + x[1]) / 2 / NORM * vp["w"])
    cy = int((y[0] + y[1]) / 2 / NORM * vp["h"])
    _flash(cx, cy)
    time.sleep(0.4)
    tag = driver.execute_script("""
        var el = document.elementFromPoint(arguments[0], arguments[1]);
        if (!el) return null;
        el.click();
        if (typeof el.focus === 'function') el.focus();
        return el.tagName + (el.type ? '[' + el.type + ']' : '');
    """, cx, cy)
    time.sleep(0.4)
    return f"clicked CSS ({cx},{cy}) -> {tag or 'nothing'}"


def type_text(text):
    el = driver.switch_to.active_element
    el.send_keys(text)
    time.sleep(0.3)
    return f"typed: {text!r}"


def press_key(key):
    key_map = {
        "Enter": Keys.RETURN, "Tab": Keys.TAB, "Escape": Keys.ESCAPE,
        "Backspace": Keys.BACK_SPACE, "ArrowDown": Keys.ARROW_DOWN, "ArrowUp": Keys.ARROW_UP,
    }
    driver.switch_to.active_element.send_keys(key_map.get(key, key))
    time.sleep(0.6)
    return f"pressed: {key}"


def scroll(direction, amount=400):
    dy = amount if direction == "down" else -amount
    driver.execute_script("window.scrollBy(0, arguments[0]);", dy)
    time.sleep(0.4)
    return f"scrolled {direction} {amount}px"


DISPATCH = {"mouse_click": mouse_click, "type_text": type_text,
            "press_key": press_key, "scroll": scroll}

TOOLS = [
    {"type": "function", "function": {
        "name": "mouse_click",
        "description": ("Click an element. Provide BOTH x and y as bounding boxes in "
                        "0-1000 normalized image coords: x:[x1,x2], y:[y1,y2]. Clicks the center."),
        "parameters": {"type": "object", "properties": {
            "x": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2},
            "y": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2}},
            "required": ["x", "y"]}}},
    {"type": "function", "function": {
        "name": "type_text",
        "description": "Type text into the currently focused element.",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {
        "name": "press_key",
        "description": "Press a key: Enter, Tab, Escape, Backspace, ArrowDown, ArrowUp.",
        "parameters": {"type": "object", "properties": {
            "key": {"type": "string"}}, "required": ["key"]}}},
    {"type": "function", "function": {
        "name": "scroll",
        "description": "Scroll the page up or down.",
        "parameters": {"type": "object", "properties": {
            "direction": {"type": "string", "enum": ["up", "down"]},
            "amount": {"type": "integer", "default": 400}}, "required": ["direction"]}}},
]

SYSTEM_PROMPT = """You are a browser agent that controls a real Chrome window through tools.
You can ONLY see the screenshot. To act, call a tool.

Coordinates: when calling mouse_click, give x and y as bounding boxes in a 0-1000
grid over the image, e.g. x:[480,520], y:[440,470]. The click lands at the center.

To search Google:
  1. mouse_click the search text box.
  2. type_text the query.
  3. press_key "Enter".
Once the results page is visible, do NOT call any tool. Reply with the single word DONE.
Take exactly one action per turn based on the CURRENT screenshot."""


# --------------------------------------------------------------------------- #
# agent loop
# --------------------------------------------------------------------------- #
def run():
    open_browser()
    driver.get("https://www.google.com")
    time.sleep(2.5)

    query = random.choice(QUERIES)
    goal = f'Search Google for: "{query}"'
    print(f"GOAL: {goal}\n")

    history = []
    for step in range(1, MAX_ACTIONS + 1):
        img_b64 = take_screenshot_b64()
        hist_txt = "\n".join(f"{i+1}. {h}" for i, h in enumerate(history)) or "None yet."
        user_msg = (f"GOAL: {goal}\n\nActions so far:\n{hist_txt}\n\n"
                    f"Looking at the current screenshot, take the next single action.")

        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg, "images": [img_b64]},
            ],
            "tools": TOOLS,
            "stream": False,
            "options": {"temperature": 0.2, "top_p": 0.95, "top_k": 64},
        }, timeout=240).json()

        msg = resp.get("message", {})
        calls = msg.get("tool_calls", [])

        if not calls:
            text = (msg.get("content") or "").strip()
            print(f"[{step}] no tool call. model said: {text!r}")
            if "DONE" in text.upper():
                print("\nTask complete.")
            else:
                print("\nStopped (model gave no action).")
            break

        fn = calls[0]["function"]
        name = fn["name"]
        args = fn.get("arguments", {})
        if isinstance(args, str):
            args = json.loads(args)

        print(f"[{step}] {name}({args})")
        handler = DISPATCH.get(name)
        if not handler:
            history.append(f"unknown tool {name}")
            continue
        try:
            result = handler(**args)
        except Exception as e:
            result = f"{name} error: {e}"
        print(f"      -> {result}")
        history.append(result)

    time.sleep(3)  # let you see the results page
    driver.quit()


if __name__ == "__main__":
    run()