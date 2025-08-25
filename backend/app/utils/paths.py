"""
Centralized Path Management for AI Chatbot
Provides consistent path configuration across the application
"""

from pathlib import Path
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class PathConfig:
    """Centralized path configuration for the application"""
    
    # Core application paths
    BACKEND_ROOT: Path
    APP_DIR: Path
    
    # Data and knowledge base paths
    DATA_DIR: Path
    INDEX_DIR: Path
    
    # Country-specific data paths
    USA_DATA_DIR: Path
    UK_DATA_DIR: Path
    AUSTRALIA_DATA_DIR: Path
    SOUTH_KOREA_DATA_DIR: Path
    
    # System paths
    CONFIG_DIR: Path
    LOGS_DIR: Path
    TOOLS_DIR: Path
    MEMORY_DIR: Path
    
    # File paths
    ENV_FILE: Path
    REQUIREMENTS_FILE: Path
    DATABASE_FILE: Path

def _build() -> PathConfig:
    """Build path configuration based on current project structure"""
    
    # Get the backend root directory (where main.py is located)
    backend_root = Path(__file__).resolve().parents[2]  # utils -> app -> backend
    
    # Get the app directory (where this file is located)
    app_dir = Path(__file__).resolve().parent.parent
    
    # Data directories
    data_dir = app_dir / "data"
    index_dir = data_dir / "index"
    
    # Country-specific data directories
    usa_data_dir = data_dir / "usa"
    uk_data_dir = data_dir / "uk"
    australia_data_dir = data_dir / "australia"
    south_korea_data_dir = data_dir / "south_korea"
    
    # System directories
    config_dir = backend_root / "config"
    logs_dir = backend_root / "logs"
    tools_dir = app_dir / "tools"
    memory_dir = app_dir / "memory"
    
    # Important files
        # Environment variables are loaded from Cloud Run, not from local files
    env_file = None
    requirements_file = backend_root / "requirements.txt"
    database_file = backend_root / "chatbot.db"
    
    # Create the configuration
    cfg = PathConfig(
        BACKEND_ROOT=backend_root,
        APP_DIR=app_dir,
        DATA_DIR=data_dir,
        INDEX_DIR=index_dir,
        USA_DATA_DIR=usa_data_dir,
        UK_DATA_DIR=uk_data_dir,
        AUSTRALIA_DATA_DIR=australia_data_dir,
        SOUTH_KOREA_DATA_DIR=south_korea_data_dir,
        CONFIG_DIR=config_dir,
        LOGS_DIR=logs_dir,
        TOOLS_DIR=tools_dir,
        MEMORY_DIR=memory_dir,
        ENV_FILE=env_file,
        REQUIREMENTS_FILE=requirements_file,
        DATABASE_FILE=database_file
    )
    
    # Ensure critical directories exist
    _ensure_directories(cfg)
    
    return cfg

def _ensure_directories(cfg: PathConfig) -> None:
    """Ensure critical directories exist"""
    critical_dirs = [
        cfg.DATA_DIR,
        cfg.INDEX_DIR,
        cfg.LOGS_DIR,
        cfg.CONFIG_DIR
    ]
    
    for directory in critical_dirs:
        directory.mkdir(parents=True, exist_ok=True)

# Global configuration instance
CFG = _build()

# Convenience functions for common path operations
def get_data_file_path(filename: str) -> Path:
    """Get path to a file in the data directory"""
    return CFG.DATA_DIR / filename

def get_index_file_path(filename: str) -> Path:
    """Get path to a file in the index directory"""
    return CFG.INDEX_DIR / filename

def get_country_data_path(country: str) -> Path:
    """Get path to country-specific data directory"""
    country_mapping = {
        'usa': CFG.USA_DATA_DIR,
        'uk': CFG.UK_DATA_DIR,
        'australia': CFG.AUSTRALIA_DATA_DIR,
        'south_korea': CFG.SOUTH_KOREA_DATA_DIR
    }
    return country_mapping.get(country.lower(), CFG.DATA_DIR)

def get_log_file_path(filename: str) -> Path:
    """Get path to a log file"""
    return CFG.LOGS_DIR / filename

def get_config_file_path(filename: str) -> Path:
    """Get path to a config file"""
    return CFG.CONFIG_DIR / filename