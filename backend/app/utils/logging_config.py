#!/usr/bin/env python3
"""
Clean Logging Configuration with Rotation and Cleanup
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import os

def setup_clean_logging(
    log_level: str = "INFO",
    log_dir: Path = None,
    max_size_mb: int = 10,
    backup_count: int = 5
):
    """
    Setup clean logging with rotation and cleanup
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        max_size_mb: Maximum log file size in MB before rotation
        backup_count: Number of backup files to keep
    """
    
    if log_dir is None:
        # Get logs directory from paths
        from .paths import CFG
        log_dir = CFG.LOGS_DIR
    
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler (simple format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # Main application log with rotation
    main_log_file = log_dir / "main_app.log"
    main_handler = logging.handlers.RotatingFileHandler(
        main_log_file,
        maxBytes=max_size_mb * 1024 * 1024,  # Convert MB to bytes
        backupCount=backup_count,
        encoding='utf-8'
    )
    main_handler.setLevel(logging.INFO)
    main_handler.setFormatter(detailed_formatter)
    main_handler.set_name("main_app")
    root_logger.addHandler(main_handler)
    
    # Error log (only errors and important)
    error_log_file = log_dir / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=max_size_mb * 1024 * 1024,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    error_handler.set_name("errors")
    root_logger.addHandler(error_handler)
    
    # Debug log (only when debug mode)
    if log_level.upper() == "DEBUG":
        debug_log_file = log_dir / "debug.log"
        debug_handler = logging.handlers.RotatingFileHandler(
            debug_log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(detailed_formatter)
        debug_handler.set_name("debug")
        root_logger.addHandler(debug_handler)
    
    # Log startup message
    logging.info("=" * 60)
    logging.info("🚀 CLEAN LOGGING SYSTEM STARTED")
    logging.info(f"📁 Log Directory: {log_dir}")
    logging.info(f"📊 Log Level: {log_level.upper()}")
    logging.info(f"📏 Max File Size: {max_size_mb}MB")
    logging.info(f"🔄 Backup Count: {backup_count}")
    logging.info(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 60)

def cleanup_old_logs(log_dir: Path = None, days_to_keep: int = 7):
    """
    Clean up old log files
    
    Args:
        log_dir: Directory containing log files
        days_to_keep: Number of days to keep logs
    """
    if log_dir is None:
        from .paths import CFG
        log_dir = CFG.LOGS_DIR
    
    if not log_dir.exists():
        return
    
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    cleaned_count = 0
    for log_file in log_dir.glob("*.log.*"):  # Rotated log files
        try:
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time < cutoff_date:
                log_file.unlink()
                cleaned_count += 1
        except Exception as e:
            print(f"Error cleaning up {log_file}: {e}")
    
    if cleaned_count > 0:
        print(f"🧹 Cleaned up {cleaned_count} old log files")

def get_log_info(log_dir: Path = None):
    """
    Get information about current log files
    
    Args:
        log_dir: Directory containing log files
    """
    if log_dir is None:
        from .paths import CFG
        log_dir = CFG.LOGS_DIR
    
    if not log_dir.exists():
        return {"error": "Log directory does not exist"}
    
    log_files = []
    total_size = 0
    
    for log_file in log_dir.glob("*.log*"):
        try:
            size = log_file.stat().st_size
            size_mb = size / (1024 * 1024)
            modified = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            log_files.append({
                "name": log_file.name,
                "size_mb": round(size_mb, 2),
                "modified": modified.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            total_size += size_mb
        except Exception as e:
            print(f"Error reading {log_file}: {e}")
    
    return {
        "log_directory": str(log_dir),
        "total_files": len(log_files),
        "total_size_mb": round(total_size, 2),
        "files": sorted(log_files, key=lambda x: x["modified"], reverse=True)
    }
