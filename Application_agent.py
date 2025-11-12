import time
import json
import re
import os  # <-- ADD THIS
from dotenv import load_dotenv  # <-- ADD THIS
import google.generativeai as genai
from playwright.sync_api import sync_playwright

# Load environment variables from .env file
load_dotenv()  # <-- ADD THIS

# ----------------------------------------------
# 1. AGENT'S HIGH-LEVEL GOAL
# -----------------------------------------------
# This is the "main objective" you give the agent.
MAIN_OBJECTIVE = """
Your goal is to find and apply for jobs.
Start by searching Google for 'software developer jobs in Texas'.
Then, look for links to job boards like LinkedIn or company career pages.
Navigate the pages, fill out all application forms using my profile,
upload my resume, and submit the application.
After one application is done, go back to the search results and find the next one.
"""

# The agent will start at Google
START_URL = "https://www.google.com"

# ----------------------------------------------
# 2. AGENT'S "MEMORY" (Your Profile)
# -----------------------------------------------
# !! IMPORTANT: UPDATE THIS SECTION !!
MY_PROFILE = {
    "first_name": "Basavaprasad",
    "last_name": "Gola",
    "email": "tobasavaprasad.com",
    "phone": "555-123-4567",
    "linkedin": "https://www.linkedin.com/in/basavaprasad-gola/",
    "github": "https://github.com/prasadgola",
    "portfolio": "https://yourportfolio.com",
    # Windows Example: 'C:\\\\Users\\\\YourUser\\\\Documents\\\\resume_v3.pdf'
    # Mac/Linux Example: '/Users/YourUser/Documents/resume_v3.pdf'
    "resume_path": "/Users/youruser/documents/resume.pdf" # Make sure this path is correct
}

# ----------------------------------------------
# 3. GEMINI API KEY
# -----------------------------------------------
# The key is now loaded from your .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file. Please create one.")
    
genai.configure(api_key=GEMINI_API_KEY)
# -----------------------------------------------


# ----------------------------------------------
# 4. LLM CONFIGURATION
# -----------------------------------------------
# We use a system prompt to give the LLM its "persona" and rules
SYSTEM_PROMPT = """
You are a helpful AI assistant that controls a web browser.
Your goal is to complete the user's main objective: {objective}

You are given a simplified version of the webpage's DOM (content) and the user's profile (memory).
Based on this information, you must decide what to do next.

Your answer MUST be a valid JSON object with two keys:
1. "thought": A brief, one-sentence explanation of your thinking.
2. "action": ONE of the following action commands:
    - "click(element_id)": Clicks on an element (like a button or link).
    - "type(element_id, 'text to type')": Types text into a field.
    - "select(element_id, 'value')": Selects an option from a dropdown.
    - "upload(element_id, 'path/to/file')": Uploads a file (use profile.resume_path).
    - "wait()": Waits for the page to load or for a few seconds.
    - "scroll('down' | 'up')": Scrolls the page.
    - "finish(report)": The task is 100% complete. Provide a summary.
    - "fail(reason)": The task cannot be completed. Explain why.

RULES:
- You can only perform ONE action at a time.
- You must use the `element_id` from the DOM provided.
- For "type" actions, use the values from the user's profile (memory) when possible.
- For "upload", the *only* file path you know is `profile.resume_path`.
- If a form is split into multiple pages, complete one page and "click" next.
- Be methodical. Fill fields one by one.
- If you get stuck, try "wait()" or "scroll('down')".
- If you are 100% finished with the *entire* objective, use "finish()".
- If you cannot complete the task, use "fail()".
"""

# We will use Gemini 1.5 Flash
generation_config = {
  "temperature": 0.2,
  "top_p": 1.0,
  "top_k": 32,
  "max_output_tokens": 4096,
  "response_mime_type": "application/json",
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    generation_config=generation_config,
    # system_instruction is the new way to pass the system prompt
    system_instruction=SYSTEM_PROMPT.format(objective=MAIN_OBJECTIVE)
)


# ----------------------------------------------
# 5. BROWSER & AGENT ACTIONS
# -----------------------------------------------

def get_simplified_dom(page):
    """
    Get a simplified, interactable DOM tree from the page.
    """
    
    # 1. Inject a script into the browser to traverse the DOM
    # This script finds all interactable elements
    page_content = page.evaluate("""
        () => {
            const interactableElements = Array.from(
                document.querySelectorAll(
                    'a, button, input:not([type="hidden"]), textarea, select, [role="button"], [role="link"], [role="menuitem"]'
                )
            );
            
            let id_counter = 1;
            const element_map = new Map();

            function getElementData(el) {
                if (element_map.has(el)) {
                    return element_map.get(el);
                }

                // Assign a unique ID
                const element_id = `id_${id_counter++}`;
                
                // Get element tag, type, and text
                const tag = el.tagName.toLowerCase();
                const type = el.getAttribute('type') || '';
                let text = el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 100);
                let placeholder = el.getAttribute('placeholder') || '';
                let label = '';

                // Try to find a label
                if (el.id) {
                    const labelEl = document.querySelector(`label[for="${el.id}"]`);
                    if (labelEl) {
                        label = labelEl.textContent.trim().replace(/\\s+/g, ' ');
                    }
                }
                if (!label && el.ariaLabel) {
                    label = el.ariaLabel;
                }
                if (!label && el.title) {
                    label = el.title;
                }

                const data = {
                    id: element_id,
                    tag: tag,
                    type: type,
                    text: text,
                    placeholder: placeholder,
                    label: label,
                    children: []
                };
                
                element_map.set(el, data);
                
                // Recursively process children
                Array.from(el.children).forEach(child => {
                    const childData = getElementData(child);
                    if (childData) {
                        data.children.push(childData);
                    }
                });
                
                return data;
            }

            // Start from the body
            const dom_tree = getElementData(document.body);
            
            // Create a mapping from our custom id back to the Playwright element
            // We can't send the real elements back, so we'll store their paths
            const id_to_path = {};
            element_map.forEach((data, el) => {
                // Create a CSS selector path
                let path = '';
                let current = el;
                while (current && current !== document.body) {
                    const id = current.id ? `#${current.id}` : '';
                    const classes = Array.from(current.classList).map(c => `.${c}`).join('');
                    const tag = current.tagName.toLowerCase();
                    
                    let nth = '';
                    if (!id && current.parentNode) {
                        const siblings = Array.from(current.parentNode.children);
                        const sameTagSiblings = siblings.filter(s => s.tagName === current.tagName);
                        if (sameTagSiblings.length > 1) {
                            const index = sameTagSiblings.indexOf(current) + 1;
                            nth = `:nth-of-type(${index})`;
                        }
                    }
                    
                    path = `${tag}${id}${classes}${nth} > ${path}`;
                    current = current.parentNode;
                }
                id_to_path[data.id] = 'body > ' + path.slice(0, -3); // Remove last ' > '
            });

            return { dom: dom_tree, paths: id_to_path };
        }
    """)
    
    return page_content['dom'], page_content['paths']

def get_llm_action(objective, dom, profile):
    """
    Get the next action from the LLM.
    """
    # Create the prompt for the LLM
    prompt = f"""
    Here is the user's profile (memory):
    {json.dumps(profile, indent=2)}

    Here is the simplified DOM of the current page:
    {json.dumps(dom, indent=2)}
    
    My main objective is: {objective}
    
    Based on the DOM and my profile, what is the single next action I should take?
    Your response must be a valid JSON object.
    """
    
    print("--- Sending prompt to Gemini ---")
    
    try:
        # Send the prompt to Gemini
        chat_session = model.start_chat()
        response = chat_session.send_message(prompt)
        
        # Parse the JSON response
        action_json = json.loads(response.text)
        
        print(f"--- Gemini's Response ---")
        print(json.dumps(action_json, indent=2))
        
        return action_json
        
    except Exception as e:
        print(f"--- Gemini Error ---")
        print(f"Error parsing Gemini response: {e}")
        print(f"Raw response was: {response.text}")
        return {"thought": "Error, retrying.", "action": "wait()"}

def execute_action(page, action_json, profile):
    """
    Executes the action decided by the LLM.
    """
    action = action_json.get('action', 'wait()')
    
    # Use regex to parse the action command
    match = re.match(r"(\w+)\((.*)\)", action)
    if not match:
        print(f"Invalid action format: {action}. Waiting.")
        time.sleep(2)
        return True

    command, args_str = match.groups()
    args = [a.strip().strip("'\"") for a in args_str.split(',')]
    
    try:
        if command == "click":
            element_id = args[0]
            selector = dom_paths.get(element_id)
            if selector:
                print(f"Action: Clicking element '{selector}'")
                page.click(selector, timeout=5000)
            else:
                print(f"Error: Could not find element with id {element_id}")

        elif command == "type":
            element_id = args[0]
            text_to_type = args[1]
            selector = dom_paths.get(element_id)
            if selector:
                print(f"Action: Typing '{text_to_type}' into '{selector}'")
                page.fill(selector, text_to_type, timeout=5000)
            else:
                print(f"Error: Could not find element with id {element_id}")

        elif command == "select":
            element_id = args[0]
            value = args[1]
            selector = dom_paths.get(element_id)
            if selector:
                print(f"Action: Selecting '{value}' in '{selector}'")
                page.select_option(selector, value, timeout=5000)
            else:
                print(f"Error: Could not find element with id {element_id}")

        elif command == "upload":
            element_id = args[0]
            file_path = profile['resume_path'] # Always use the profile's resume path
            selector = dom_paths.get(element_id)
            if selector:
                print(f"Action: Uploading '{file_path}' to '{selector}'")
                page.set_input_files(selector, file_path, timeout=10000)
            else:
                print(f"Error: Could not find element with id {element_id}")

        elif command == "wait":
            print("Action: Waiting for 2 seconds...")
            time.sleep(2)
            
        elif command == "scroll":
            direction = args[0]
            if direction == "down":
                print("Action: Scrolling down")
                page.evaluate("window.scrollBy(0, window.innerHeight)")
            elif direction == "up":
                print("Action: Scrolling up")
                page.evaluate("window.scrollBy(0, -window.innerHeight)")
            time.sleep(1)
            
        elif command == "finish":
            print(f"Action: Task finished! Summary: {args_str}")
            return False # Stop the loop
            
        elif command == "fail":
            print(f"Action: Task failed! Reason: {args_str}")
            return False # Stop the loop
            
        else:
            print(f"Unknown command: {command}. Waiting.")
            time.sleep(2)

    except Exception as e:
        print(f"Error executing action '{action}': {e}")
        print("Continuing...")
    
    return True # Continue the loop


# ----------------------------------------------
# 6. THE MAIN AGENT LOOP
# -----------------------------------------------
def run_agent():
    
    global dom_paths # Make paths globally accessible to execute_action
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        print("Agent starting... Press Enter in this terminal to begin.")
        print("Once running, press Ctrl+C in this terminal to stop.")
        input() # Waits for you to press Enter
        
        page.goto(START_URL)
        
        try:
            # This is the main loop. It runs forever until you Ctrl+C.
            while True:
                print("\n" + "="*50)
                
                # 1. EYES: See the page
                dom, dom_paths = get_simplified_dom(page)
                
                # 2. BRAIN: Decide what to do
                action = get_llm_action(MAIN_OBJECTIVE, dom, MY_PROFILE)
                
                # 3. HANDS: Do the action
                if not execute_action(page, action, MY_PROFILE):
                    break # Exit loop if action was "finish" or "fail"
                
        except KeyboardInterrupt:
            print("\n" + "="*50)
            print(">>> User pressed Ctrl+C. Shutting down agent. <<<")
        except Exception as e:
            print(f"\nFATAL ERROR: {e}")
        finally:
            print("Closing browser.")
            browser.close()

# --- Run the Agent ---
if __name__ == "__main__":
    run_agent()