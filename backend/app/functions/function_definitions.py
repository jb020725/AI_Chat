"""
Function Definitions for Gemini Native Function Calling

Defines the schema for functions that the LLM can call to:
1. Collect contact information for Lakehead Education follow-up
2. Search country-specific visa information for Nepali students
3. Qualify leads based on conversation for Lakehead Education services
"""

FUNCTIONS = [




    {
        "name": "handle_contact_request",
        "description": "Smart contact request handler that detects both lead opportunities and urgent contact needs. Use when user shows serious intent (wants to apply, needs guidance) OR shows extreme urgency (needs immediate call, emergency situation).",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's current question or statement to analyze"
                },
                "conversation_context": {
                    "type": "object",
                    "description": "Current conversation context and user's expressed interests"
                },
                "detected_interests": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of detected interests (country, program, intake, etc.)"
                },
                "urgency_level": {
                    "type": "string",
                    "description": "Detected urgency level (normal, urgent, extreme, emergency)",
                    "enum": ["normal", "urgent", "extreme", "emergency"]
                }
            },
            "required": ["user_query", "conversation_context"]
        }
    },
    {
        "name": "detect_and_save_contact_info",
        "description": "Automatically detect, extract, and save contact information from user messages. Use when user provides any contact details (name, email, phone, country, intake) either voluntarily or after being asked. This function handles both initial contact info and updates to existing info.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's current message to analyze for contact information"
                },
                "conversation_context": {
                    "type": "object",
                    "description": "Current conversation context and previously saved information"
                },
                "extraction_mode": {
                    "type": "string",
                    "description": "Mode of contact info extraction",
                    "enum": ["auto_detect", "update_existing", "initial_contact"]
                }
            },
            "required": ["user_query", "conversation_context"]
        }
    },
    {
        "name": "define_response_strategy",
        "description": "Define response strategy when RAG returns no results. Student visa topics from Nepal to USA, UK, South Korea, Australia only.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_query": {
                    "type": "string",
                    "description": "User's question to analyze for response strategy"
                },
                "rag_results_count": {
                    "type": "integer",
                    "description": "Number of results from RAG search (0 means no results)"
                },
                "session_memory": {
                    "type": "object",
                    "description": "User's session memory and conversation history"
                }
            },
            "required": ["user_query", "rag_results_count"]
        }
    },


]

# Function metadata for easier access
FUNCTION_METADATA = {




    "handle_contact_request": {
        "priority": "high",
        "trigger_keywords": ["i want to apply", "i am applying", "ready to apply", "looking for guidance", "need guidance", "lakehead", "your company", "call me", "contact me", "representative", "advisor", "office visit", "process my visa", "handle my application", "march intake", "fall intake", "spring intake", "deadline", "timeline", "urgent", "emergency", "extreme", "immediate", "talk to someone", "need help now", "call me now"],
        "description": "Smart contact handler that detects both lead opportunities (serious intent) and urgent contact needs (emergency, immediate help). Routes appropriately based on urgency level."
    },
    "detect_and_save_contact_info": {
        "priority": "high",
        "trigger_keywords": ["my name is", "i am", "i'm", "email is", "my email", "phone is", "my phone", "number is", "my number", "interested in", "want to go to", "planning for", "for fall", "for spring", "for march", "usa", "uk", "australia", "south korea", "bachelor", "master", "phd", "doctorate"],
        "description": "Automatically detects and saves contact information from user messages. Handles both initial contact info and updates to existing information."
    },
    "define_response_strategy": {
        "priority": "high",
        "trigger_keywords": ["what", "how", "when", "where", "which", "information", "details", "requirements", "process", "costs", "intakes", "universities", "visa", "study", "requirements", "documents"],
        "description": "Defines response strategy when RAG has no results. Ensures appropriate handling of student visa topics and off-topic questions."
    },


}
