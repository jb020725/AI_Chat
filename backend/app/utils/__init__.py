"""
Utility modules for AI Chatbot
Provides centralized path management, logging, and common utilities
"""

from .paths import CFG, get_data_file_path, get_index_file_path, get_country_data_path, get_log_file_path, get_config_file_path
from .logging_config import setup_clean_logging, cleanup_old_logs, get_log_info

__all__ = [
    'CFG',
    'get_data_file_path',
    'get_index_file_path', 
    'get_country_data_path',
    'get_log_file_path',
    'get_config_file_path',
    'setup_clean_logging',
    'cleanup_old_logs',
    'get_log_info'
]
