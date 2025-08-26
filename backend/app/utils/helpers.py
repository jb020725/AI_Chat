"""
Helper utilities for the AI Chatbot
Common functions used across the application
"""

import logging
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)



def validate_file_path(file_path: Path) -> bool:
    """Validate if a file path exists and is accessible"""
    try:
        return file_path.exists() and file_path.is_file() and os.access(file_path, os.R_OK)
    except Exception as e:
        logger.error(f"Error validating file path {file_path}: {e}")
        return False

def safe_json_load(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely load JSON file with error handling"""
    try:
        if validate_file_path(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return None

def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes"""
    try:
        if file_path.exists():
            return file_path.stat().st_size / (1024 * 1024)
        return 0.0
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {e}")
        return 0.0

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display"""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    import re
    # Remove or replace unsafe characters
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return safe_filename[:255]  # Limit length

def detect_detailed_response_request(message: str) -> bool:
    """
    Detect if user is requesting detailed information
    
    Args:
        message: User's message
        
    Returns:
        bool: True if user wants detailed response, False for brief response
    """
    detailed_phrases = [
        "tell me more",
        "can you explain",
        "what are the details",
        "i need more information",
        "please elaborate",
        "how does this work",
        "what are the steps",
        "can you break this down",
        "give me the full process",
        "explain in detail",
        "more details",
        "detailed explanation",
        "step by step",
        "walk me through",
        "describe the process",
        "what's involved",
        "how do i",
        "what do i need to do",
        "break it down",
        "in detail"
    ]
    
    message_lower = message.lower()
    return any(phrase in message_lower for phrase in detailed_phrases)

def get_response_length_instruction(message: str) -> str:
    """
    Get response length instruction based on user message
    
    Args:
        message: User's message
        
    Returns:
        str: Response length instruction for the prompt
    """
    if detect_detailed_response_request(message):
        return "EXPAND: User is requesting detailed information. Provide comprehensive response with bullet points and step-by-step guidance."
    else:
        return "BRIEF: Keep response short and concise (2-3 sentences maximum). Offer to provide more details if needed."
