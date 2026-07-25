"""
Log Filters
============

Filters that prevent sensitive data from appearing in logs.
"""

import logging
import re
from typing import List


class SecretMaskingFilter(logging.Filter):
    """
    Filter that masks sensitive information in log records.
    
    Detects and replaces patterns that look like:
    - SSH private keys
    - Passwords
    - API tokens
    - AWS secret ARNs values
    - JWT tokens
    """
    
    # Patterns to mask in log messages
    PATTERNS: List[re.Pattern] = [
        # SSH private keys
        re.compile(
            r"-----BEGIN[A-Z ]*PRIVATE KEY-----.*?-----END[A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        # Password-like fields in key=value format
        re.compile(
            r"(password|passwd|secret|token|api_key|private_key)"
            r"\s*[=:]\s*\S+",
            re.IGNORECASE,
        ),
        # JWT tokens
        re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
        # AWS Secret ARN values (mask the value after ARN references)
        re.compile(
            r"(arn:aws:secretsmanager:[^:]+:[^:]+:secret:[^\s]+)",
            re.IGNORECASE,
        ),
    ]
    
    MASK = "***REDACTED***"
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Mask sensitive data in the log record message.
        
        Always returns True (record is never filtered out),
        but the message content is sanitized.
        """
        if record.msg:
            record.msg = self._mask_message(str(record.msg))
        
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._mask_message(str(v))
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._mask_message(str(a)) for a in record.args
                )
        
        return True
    
    def _mask_message(self, message: str) -> str:
        """Apply all masking patterns to a message."""
        for pattern in self.PATTERNS:
            message = pattern.sub(self.MASK, message)
        return message
