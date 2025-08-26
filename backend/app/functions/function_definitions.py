"""
Function Definitions for Clean Function-Calling Structure

Defines the schema for focused, deterministic tools that the LLM can call:
1. get_answer - Serve vetted content only
2. qualify_interest - Lightweight lead intent capture
3. request_consent - Explicit consent before PII collection
4. save_lead - Store contact after consent

6. notify_human - CRM handoff
"""

FUNCTIONS = [
    {
        "name": "get_answer",
        "description": "Return a vetted answer snippet about student visas or the consultancy. Use this for ALL information requests - do not invent answers.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": [
                        "visa_overview", "intakes_general", "eligibility_basics", "required_documents",
                        "processing_times", "financial_proof_basics", "consultancy_services",
                        "fees_and_packages", "office_locations", "working_hours", "contact_options",
                        "privacy_policy", "disclaimer", "usa_visa", "uk_visa", "australia_visa", "south_korea_visa"
                    ],
                    "description": "Specific topic to get vetted information about"
                },
                "locale": {
                    "type": "string",
                    "description": "BCP-47 code like en-US, en-GB, ko-KR",
                    "default": "en-US"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "qualify_interest",
        "description": "Capture non-PII interest to personalize follow-ups. Use when user shows interest but hasn't provided contact details yet.",
        "parameters": {
            "type": "object",
            "properties": {
                "study_country": {
                    "type": "string",
                    "enum": ["USA", "UK", "Australia", "South Korea", "Other"],
                    "description": "Country the user is interested in studying in"
                },
                "study_level": {
                    "type": "string",
                    "enum": ["Bachelors", "Masters", "PhD", "Diploma", "Other"],
                    "description": "Level of study the user is interested in"
                },
                "target_intake": {
                    "type": "string",
                    "description": "Target intake period, e.g., 2026-Fall, 2026-Spring, Unknown"
                },
                "notes": {
                    "type": "string",
                    "maxLength": 300,
                    "description": "Additional context about user's interest"
                }
            },
            "required": ["study_country"]
        }
    },
    {
        "name": "request_consent",
        "description": "Record explicit user consent to store and contact them. REQUIRED before collecting any contact information.",
        "parameters": {
            "type": "object",
            "properties": {
                "consent_text_version": {
                    "type": "string",
                    "description": "Version of consent text shown to user"
                },
                "consent": {
                    "type": "boolean",
                    "description": "Whether user explicitly consented (true) or declined (false)"
                }
            },
            "required": ["consent_text_version", "consent"]
        }
    },
    {
        "name": "save_lead",
        "description": "Save lead with contact details after explicit consent has been given. Only call after request_consent returns true.",
        "parameters": {
            "type": "object",
            "properties": {
                "full_name": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 80,
                    "description": "User's full name"
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "User's email address"
                },
                "phone_e164": {
                    "type": "string",
                    "pattern": "^\\+?[1-9]\\d{7,14}$",
                    "description": "Phone number in E.164 format (e.g., +977123456789)"
                },
                "preferred_channel": {
                    "type": "string",
                    "enum": ["phone", "whatsapp", "telegram", "email"],
                    "description": "User's preferred contact method"
                },
                "study_country": {
                    "type": "string",
                    "description": "Country of interest (from qualify_interest)"
                },
                "study_level": {
                    "type": "string",
                    "description": "Study level (from qualify_interest)"
                },
                "target_intake": {
                    "type": "string",
                    "description": "Target intake (from qualify_interest)"
                },
                "notes": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Additional notes about the lead"
                },
                "consent_text_version": {
                    "type": "string",
                    "description": "Version of consent text that was agreed to"
                },
                "consent_timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "When consent was given (ISO 8601 format)"
                }
            },
            "required": ["full_name", "consent_text_version", "consent_timestamp"]
        }
    },

    {
        "name": "notify_human",
        "description": "Ping advisors with a concise summary. Call this after save_lead to notify human advisors.",
        "parameters": {
            "type": "object",
            "properties": {
                "lead_id": {
                    "type": "string",
                    "description": "ID of the lead that was created"
                },
                "summary": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Concise summary of user goals and needs (≤20 words recommended)"
                },
                "priority": {
                    "type": "string",
                    "enum": ["normal", "high"],
                    "description": "Priority level for human attention"
                }
            },
            "required": ["summary"]
        }
    }
]

# Function metadata for easier access
FUNCTION_METADATA = {
    "get_answer": {
        "priority": "high",
        "description": "Primary information source - use for ALL visa/consultancy questions",
        "usage": "Call this first for any information request before offering contact options"
    },
    "qualify_interest": {
        "priority": "medium",
        "description": "Capture interest when user shows intent but no contact details",
        "usage": "Use when user mentions specific countries, programs, or intakes"
    },
    "request_consent": {
        "priority": "high",
        "description": "REQUIRED before collecting any contact information",
        "usage": "Always call this before save_lead to ensure compliance"
    },
    "save_lead": {
        "priority": "high",
        "description": "Save contact details after explicit consent",
        "usage": "Only call after request_consent returns true"
    },

    "notify_human": {
        "priority": "medium",
        "description": "Notify human advisors about new leads",
        "usage": "Call after save_lead for CRM handoff"
    }
}
