"""
Log Formatters
==============

JSON and text formatters for structured logging output.
"""

import json
import logging
import traceback
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON lines.
    
    Produces machine-parseable structured log output suitable
    for log aggregation systems (ELK, CloudWatch, etc.).
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Include extra fields
        if hasattr(record, "hostname"):
            log_data["hostname"] = record.hostname
        if hasattr(record, "server_id"):
            log_data["server_id"] = record.server_id
        
        # Include any extra attributes passed via `extra={}`
        standard_attrs = {
            "name", "msg", "args", "created", "relativeCreated",
            "exc_info", "exc_text", "stack_info", "lineno",
            "funcName", "levelno", "filename", "module",
            "pathname", "process", "processName", "thread",
            "threadName", "taskName", "message", "levelname",
            "msecs",
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                try:
                    json.dumps(value)  # Ensure serializable
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        # Include exception info
        if record.exc_info:
            log_data["exception"] = traceback.format_exception(
                *record.exc_info
            )
        
        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development use.
    """
    
    FORMAT = (
        "%(asctime)s | %(levelname)-8s | %(name)-12s | "
        "%(module)s:%(funcName)s:%(lineno)d | %(message)s"
    )
    
    def __init__(self):
        super().__init__(fmt=self.FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
