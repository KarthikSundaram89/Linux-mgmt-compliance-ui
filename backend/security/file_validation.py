"""
File Upload & CSV Import Security
==================================

Validates uploaded files and sanitizes CSV imports
to prevent injection attacks and malicious content.
"""

import csv
import io
import os
import re
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Allowed file types for upload
ALLOWED_EXTENSIONS = frozenset([".csv", ".json", ".txt"])
ALLOWED_MIME_TYPES = frozenset([
    "text/csv",
    "text/plain",
    "application/json",
    "application/octet-stream",
])

# Maximum file sizes
MAX_CSV_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

# CSV column limits
MAX_CSV_COLUMNS = 50
MAX_CSV_ROWS = 10000
MAX_FIELD_LENGTH = 1000

# Patterns indicating CSV injection
CSV_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def validate_file_upload(
    filename: str,
    content_type: str,
    file_size: int,
    max_size: int = MAX_UPLOAD_SIZE,
) -> Tuple[bool, Optional[str]]:
    """
    Validate an uploaded file.

    Checks extension, content type, and size.
    Generates a safe random filename.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File type '{ext}' not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}"

    # Check content type
    if content_type not in ALLOWED_MIME_TYPES:
        return False, f"Content type '{content_type}' not allowed"

    # Check size
    if file_size > max_size:
        return False, f"File too large ({file_size} bytes). Maximum: {max_size} bytes"

    # Check for directory traversal in filename
    if ".." in filename or "/" in filename or "\\" in filename:
        return False, "Invalid filename (directory traversal attempt)"

    return True, None


def generate_safe_filename(original_filename: str) -> str:
    """
    Generate a safe random filename preserving the extension.

    Prevents directory traversal and filename-based attacks.
    """
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".dat"
    random_name = secrets.token_urlsafe(16)
    return f"{random_name}{ext}"


def validate_csv_import(
    content: bytes,
    required_headers: Optional[List[str]] = None,
) -> Tuple[bool, Optional[str], List[Dict[str, Any]]]:
    """
    Validate and sanitize a CSV file for import.

    Checks:
    - File size
    - Encoding (UTF-8)
    - Headers present and valid
    - Row count within limits
    - Field length within limits
    - No CSV injection characters

    Returns:
        Tuple of (is_valid, error_message, sanitized_rows).
    """
    # Size check
    if len(content) > MAX_CSV_SIZE:
        return False, f"CSV too large ({len(content)} bytes)", []

    # Decode
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except Exception:
            return False, "Unable to decode CSV (must be UTF-8)", []

    # Parse
    try:
        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames

        if not headers:
            return False, "CSV has no headers", []

        # Validate headers
        if len(headers) > MAX_CSV_COLUMNS:
            return False, f"Too many columns ({len(headers)})", []

        if required_headers:
            missing = set(required_headers) - set(headers)
            if missing:
                return False, f"Missing required headers: {missing}", []

        # Validate and sanitize rows
        rows: List[Dict[str, Any]] = []
        for i, row in enumerate(reader):
            if i >= MAX_CSV_ROWS:
                return False, f"Too many rows (max {MAX_CSV_ROWS})", []

            sanitized = {}
            for key, value in row.items():
                if value is None:
                    sanitized[key] = ""
                    continue

                # Length check
                if len(value) > MAX_FIELD_LENGTH:
                    return False, (
                        f"Field too long in row {i+1}, "
                        f"column '{key}' ({len(value)} chars)"
                    ), []

                # CSV injection check
                sanitized[key] = sanitize_csv_value(value)

            rows.append(sanitized)

        return True, None, rows

    except csv.Error as e:
        return False, f"CSV parse error: {str(e)}", []


def sanitize_csv_value(value: str) -> str:
    """
    Sanitize a single CSV field value.

    Prevents CSV injection by removing dangerous prefixes.
    """
    stripped = value.strip()

    # Remove CSV injection prefixes
    if stripped and stripped[0] in CSV_INJECTION_PREFIXES:
        stripped = "'" + stripped  # Prefix with single quote

    # Remove null bytes
    stripped = stripped.replace("\x00", "")

    return stripped
