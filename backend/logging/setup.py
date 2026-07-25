"""
Logging Configuration
=====================

Sets up structured logging with:
- Separate log files (app, collector, scheduler, security, audit)
- JSON or text formatting
- Automatic rotation based on file size
- Compression of rotated logs
- Secret masking filter
"""

import logging
import logging.handlers
import os
from typing import Optional

from backend.logging.formatters import JSONFormatter, TextFormatter
from backend.logging.filters import SecretMaskingFilter
from backend.settings.config import Settings


# Log file definitions: logger_name -> filename
LOG_FILES = {
    "app": "app.log",
    "collector": "collector.log",
    "scheduler": "scheduler.log",
    "security": "security.log",
    "audit": "audit.log",
}


def setup_logging(settings: Settings) -> None:
    """
    Configure the application logging system.
    
    Creates separate log files for different concerns,
    applies formatting, rotation, and secret masking.
    
    Args:
        settings: Application settings with log configuration.
    """
    # Ensure log directory exists
    log_dir = settings.log_dir
    os.makedirs(log_dir, exist_ok=True)
    
    # Select formatter
    if settings.log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    
    # Add secret masking filter to all handlers
    secret_filter = SecretMaskingFilter()
    
    # Console handler (always active)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(secret_filter)
    root_logger.addHandler(console_handler)
    
    # File handlers for each log category
    for logger_name, filename in LOG_FILES.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, settings.log_level))
        logger.propagate = False
        
        # Rotating file handler
        file_path = os.path.join(str(log_dir), filename)
        max_bytes = settings.log_max_size_mb * 1024 * 1024
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=file_path,
            maxBytes=max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(secret_filter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    logging.getLogger("app").info(
        "Logging configured",
        extra={
            "log_level": settings.log_level,
            "log_format": settings.log_format,
            "log_dir": str(log_dir),
        },
    )
