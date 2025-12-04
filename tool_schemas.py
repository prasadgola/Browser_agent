# ============================================================
# BROWSER TOOLS - OpenAI-compatible format for GPT-OSS
# ============================================================
BROWSER_TOOLS = [
    # ----------------------------------------------------------
    # NAVIGATION TOOLS
    # ----------------------------------------------------------
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "open_browser",
    #         "description": "Opens a new browser window. Must be called first before any other browser action.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {},
    #             "required": []
    #         }
    #     }
    # },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "open_url",
    #         "description": "Navigate the browser to a specific URL. Browser must be open first.",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "url": {
    #                     "type": "string",
    #                     "description": "The full URL to navigate to (e.g., 'https://google.com')"
    #                 }
    #             },
    #             "required": ["url"]
    #         }
    #     }
    # },
    {
        "type": "function",
        "function": {
            "name": "go_back",
            "description": "Navigate back to the previous page in browser history.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll the page in a specified direction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down", "top", "bottom"],
                        "description": "Direction to scroll: 'up', 'down', 'top' (page start), 'bottom' (page end)"
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Pixels to scroll (only for 'up'/'down'). Default is 500."
                    }
                },
                "required": ["direction"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "switch_tab",
            "description": "Switch to a different browser tab by index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tab_index": {
                        "type": "integer",
                        "description": "Index of the tab to switch to. Use -1 for the last/newest tab. Default is -1."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_tab",
            "description": "Close the current browser tab and switch to the previous one.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_browser",
            "description": "Close the browser completely. Call this when the task is finished.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },

    # ----------------------------------------------------------
    # INTERACTION TOOLS
    # ----------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click on an element by its index from get_page_state(). The element will be scrolled into view automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "The index number of the element to click (from get_page_state output, e.g., [0], [1], [2])"
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
            "description": "Force click an element using JavaScript. Use when regular click() fails on hidden or overlay elements.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "The index number of the element to click"
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
            "description": "Type text into an input field or textarea.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "The index number of the input element to type into"
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to type into the element"
                    },
                    "clear_first": {
                        "type": "boolean",
                        "description": "Whether to clear existing text before typing. Default is true."
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
            "description": "Press a keyboard key. Useful for Enter to submit, Tab to move focus, Escape to close dialogs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "enum": ["enter", "tab", "escape", "backspace", "down", "up"],
                        "description": "The key to press: 'enter', 'tab', 'escape', 'backspace', 'down', 'up'"
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
            "description": "Hover over an element to trigger dropdowns, tooltips, or menus.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "The index number of the element to hover over"
                    }
                },
                "required": ["element_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "select_option",
            "description": "Select an option from a dropdown/select element.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "The index number of the <select> element"
                    },
                    "visible_text": {
                        "type": "string",
                        "description": "The visible text of the option to select (preferred method)"
                    },
                    "value": {
                        "type": "string",
                        "description": "The value attribute of the option to select"
                    },
                    "index": {
                        "type": "integer",
                        "description": "The index of the option (0-based)"
                    }
                },
                "required": ["element_index"]
            }
        }
    },

    # ----------------------------------------------------------
    # OBSERVATION TOOLS
    # ----------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "get_page_state",
            "description": "Get the current page state including all interactive elements with their indices. ALWAYS call this after navigating, clicking, or scrolling to see the updated page. Returns element indices needed for click(), type_text(), etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_text": {
                        "type": "boolean",
                        "description": "If true, include the full page text content. Default is false."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_text",
            "description": "Get the text content of a specific element.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "The index number of the element to get text from"
                    }
                },
                "required": ["element_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_text",
            "description": "Get all visible text content on the page (not just interactive elements). Useful for reading articles or extracting information.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait_for_element",
            "description": "Wait for a specific element to appear on the page using CSS selector.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the element to wait for (e.g., '#submit-btn', '.login-form')"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum seconds to wait. Default is 10."
                    }
                },
                "required": ["selector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait_for_page_load",
            "description": "Wait for the page to fully load (document.readyState === 'complete').",
            "parameters": {
                "type": "object",
                "properties": {
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum seconds to wait. Default is 10."
                    }
                },
                "required": []
            }
        }
    },

    # ----------------------------------------------------------
    # SPECIAL TOOLS
    # ----------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "upload_file",
            "description": "Upload a file to a file input element. The element must be an <input type='file'>.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "The index number of the file input element"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file to upload (e.g., '/home/user/resume.pdf')"
                    }
                },
                "required": ["element_index", "file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "handle_alert",
            "description": "Handle a JavaScript alert/confirm/prompt dialog.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["accept", "dismiss"],
                        "description": "Action to take: 'accept' (OK) or 'dismiss' (Cancel). Default is 'accept'."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "switch_to_iframe",
            "description": "Switch focus to an iframe or back to main content. Many forms are inside iframes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_index": {
                        "type": "integer",
                        "description": "Index of the iframe element to switch to. Omit or set null to switch back to main content."
                    }
                },
                "required": []
            }
        }
    },

    # ----------------------------------------------------------
    # TASK COMPLETION
    # ----------------------------------------------------------
    {
        "type": "function",
        "function": {
            "name": "task_complete",
            "description": "Signal that the task has been completed successfully. Call this when the user's request has been fulfilled.",
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
            "description": "Signal that the task could not be completed. Call this when encountering an unrecoverable error.",
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
    }
]