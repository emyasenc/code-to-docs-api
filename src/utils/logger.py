# src/utils/logger.py
"""
Logging configuration for the Code-to-Docs API.
Provides structured logging for production and debug environments.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path


# Log format for readability
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def get_log_level() -> str:
    """Get log level from environment variable, default to INFO"""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    if level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        return level
    return "INFO"


def setup_logger(
    name: str,
    log_file: str = None,
    level: str = None,
    console: bool = True
) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Name of log file (without path)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console: Whether to log to console
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    log_level = level or get_log_level()
    logger.setLevel(getattr(logging, log_level))
    
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Console handler (for development and Render logs)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler (for persistent logs)
    if log_file:
        log_path = LOG_DIR / f"{log_file}.log"
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10_485_760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Simple logger factory for use in modules.
    
    Usage:
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Hello world")
    """
    return setup_logger(name, log_file=name.replace(".", "_"))