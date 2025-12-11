BROWSER_TOOLS = [
    # === NAVIGATION (2) ===
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll the page. Essential for viewing more contacts, posts, or messages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down", "top", "bottom"],
                        "description": "Direction: 'up', 'down', 'top', 'bottom'"
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Pixels to scroll for up/down. Default 500."
                    }
                },
                "required": ["direction"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "go_back",
            "description": "Navigate back to previous page.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    
    # === INTERACTION (5) ===
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click an element by its index from get_page_state(). Element is automatically scrolled into view.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "Index from get_page_state(): [0], [1], [2], etc."
                    }
                },
                "required": ["element_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "js_click",
            "description": "Force click using JavaScript. Use when regular click() fails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "Index of element to click"
                    }
                },
                "required": ["element_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text into input fields or contenteditable divs (WhatsApp/LinkedIn message boxes).",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "Index of input element"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type"
                    },
                    "clear_first": {
                        "type": "boolean",
                        "description": "Clear existing text first. Default true."
                    }
                },
                "required": ["element_index", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a keyboard key. Use 'enter' to send messages or submit forms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "enum": ["enter", "tab", "escape", "backspace", "down", "up"],
                        "description": "Key to press"
                    }
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hover",
            "description": "Hover over an element to reveal dropdown menus or tooltips. Essential for LinkedIn 'Connect' button.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "Index of element to hover over"
                    }
                },
                "required": ["element_index"]
            }
        }
    },
    
    # === SMART TOOLS (3) ===
    {
        "type": "function",
        "function": {
            "name": "get_page_state",
            "description": "Get current page state showing all interactive elements with indices. ALWAYS call this first and after navigation/clicks to see what's available.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_text": {
                        "type": "boolean",
                        "description": "Include full page text. Default false."
                    },
                    "verbosity": {
                        "type": "string",
                        "enum": ["minimal", "normal", "detailed"],
                        "description": "Detail level. Auto-adjusts for complex apps. Default 'normal'."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_elements_by_text",
            "description": "Search for elements containing specific text. Returns indices you can use with click(). Perfect for finding contacts or profiles by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to search for (case-insensitive, partial match)"
                    },
                    "element_type": {
                        "type": "string",
                        "enum": ["button", "link", "input", "listitem"],
                        "description": "Optional: Filter results by element type"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_element_with_text",
            "description": "Find and click element with specific text in one operation. Best for clicking buttons or contacts by visible text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to find and click (e.g., 'Connect', 'John Smith', 'Send')"
                    }
                },
                "required": ["text"]
            }
        }
    },
    
    # === SPECIAL (2) ===
    {
        "type": "function", 
        "function": {
            "name": "upload_file_auto",
            "description": "Upload a file on any website. Just provide the filename - it searches Documents, Downloads, Desktop automatically. Use this INSTEAD of clicking file picker buttons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Filename ('resume.pdf'), relative path ('docs/resume.pdf'), or full path ('~/Documents/resume.pdf')"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "handle_alert",
            "description": "Handle JavaScript alert/confirm/prompt dialogs. LinkedIn sometimes shows confirmation popups.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["accept", "dismiss"],
                        "description": "'accept' (OK button) or 'dismiss' (Cancel button). Default 'accept'."
                    }
                },
                "required": []
            }
        }
    },
    
    # === COMPLETION (2) ===
    {
        "type": "function",
        "function": {
            "name": "task_complete",
            "description": "Signal that the task has been completed successfully.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Summary of what was accomplished"
                    }
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_failed",
            "description": "Signal that the task could not be completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Explanation of why the task failed"
                    }
                },
                "required": ["reason"]
            }
        }
    },
]