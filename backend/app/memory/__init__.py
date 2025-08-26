"""
Memory Management System for Chatbot
Handles session memory, user info tracking, and smart response generation
"""

from .session_memory import SessionMemory, get_session_memory
from .smart_response import SmartResponse, smart_response

__all__ = [
    'SessionMemory',
    'get_session_memory',
    'SmartResponse', 
    'smart_response'
]
