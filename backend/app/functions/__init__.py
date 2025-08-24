"""
Function Calling Module for AI Chatbot

This module handles Gemini native function calling for:
- Contact information collection
- Country-specific searches  
- Lead qualification
"""

from .function_definitions import FUNCTIONS
from .function_handlers import FunctionHandler
from .function_integrator import FunctionIntegrator

__all__ = [
    'FUNCTIONS',
    'FunctionHandler', 
    'FunctionIntegrator'
]
