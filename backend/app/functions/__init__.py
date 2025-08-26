"""
Function Calling Module for AI Chatbot

eThis module handles clean, focused function calling for:
- Vetted content lookup (get_answer)
- Interest qualification (qualify_interest)
- Consent management (request_consent)
- Lead capture (save_lead)

- Human notification (notify_human)
"""

from .function_definitions import FUNCTIONS, FUNCTION_METADATA
from .function_handlers import function_handler
from .function_integrator import FunctionIntegrator

__all__ = [
    'FUNCTIONS',
    'FUNCTION_METADATA',
    'function_handler', 
    'FunctionIntegrator'
]
