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
