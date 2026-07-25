"""
Password Policy Enforcement
============================

Enterprise password requirements:
- Minimum length (12 characters)
- Complexity (upper, lower, digit, special)
- History (prevent reuse of last N passwords)
- Expiration (configurable max age)
- Common password rejection
"""

import hashlib
import re
from typing import List, Optional, Tuple


# Minimum password requirements
MIN_LENGTH = 12
MAX_LENGTH = 128
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGIT = True
REQUIRE_SPECIAL = True
PASSWORD_HISTORY_COUNT = 5

# Common weak passwords to reject (subset)
COMMON_PASSWORDS = frozenset([
    "password", "password1", "password123", "12345678",
    "qwerty", "admin", "letmein", "welcome",
    "changeme", "p@ssw0rd", "pass1234", "default",
    "admin123", "root", "toor", "123456789",
    "abc123", "monkey", "master", "dragon",
])


def validate_password_strength(
    password: str,
    username: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate password meets enterprise security requirements.

    Args:
        password: The password to validate.
        username: Optional username to check against.

    Returns:
        Tuple of (is_valid, list_of_violations).
    """
    violations: List[str] = []

    # Length check
    if len(password) < MIN_LENGTH:
        violations.append(
            f"Password must be at least {MIN_LENGTH} characters"
        )
    if len(password) > MAX_LENGTH:
        violations.append(
            f"Password must not exceed {MAX_LENGTH} characters"
        )

    # Complexity checks
    if REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        violations.append(
            "Password must contain at least one uppercase letter"
        )
    if REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        violations.append(
            "Password must contain at least one lowercase letter"
        )
    if REQUIRE_DIGIT and not re.search(r"\d", password):
        violations.append(
            "Password must contain at least one digit"
        )
    if REQUIRE_SPECIAL and not re.search(
        r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password
    ):
        violations.append(
            "Password must contain at least one special character"
        )

    # Username check
    if username and username.lower() in password.lower():
        violations.append(
            "Password must not contain your username"
        )

    # Common password check
    if password.lower() in COMMON_PASSWORDS:
        violations.append(
            "Password is too common and easily guessable"
        )

    # Sequential characters check
    if _has_sequential_chars(password, 4):
        violations.append(
            "Password must not contain 4+ sequential characters"
        )

    # Repeated characters check
    if _has_repeated_chars(password, 4):
        violations.append(
            "Password must not contain 4+ repeated characters"
        )

    return len(violations) == 0, violations


def hash_for_history(password: str) -> str:
    """
    Create a non-reversible hash for password history comparison.

    Uses SHA-256 with a fixed salt for history checking only.
    Actual password storage uses argon2/bcrypt.
    """
    return hashlib.sha256(
        f"pw_history:{password}".encode()
    ).hexdigest()


def check_password_history(
    password: str, history_hashes: List[str]
) -> bool:
    """
    Check if a password was recently used.

    Args:
        password: The new password candidate.
        history_hashes: Previous password hashes.

    Returns:
        True if password is NOT in history (allowed).
    """
    current_hash = hash_for_history(password)
    return current_hash not in history_hashes


def _has_sequential_chars(password: str, length: int) -> bool:
    """Check for sequential characters (abc, 123, etc.)."""
    for i in range(len(password) - length + 1):
        chunk = password[i:i + length]
        # Check ascending
        if all(
            ord(chunk[j + 1]) - ord(chunk[j]) == 1
            for j in range(len(chunk) - 1)
        ):
            return True
        # Check descending
        if all(
            ord(chunk[j]) - ord(chunk[j + 1]) == 1
            for j in range(len(chunk) - 1)
        ):
            return True
    return False


def _has_repeated_chars(password: str, length: int) -> bool:
    """Check for repeated characters (aaaa, 1111, etc.)."""
    for i in range(len(password) - length + 1):
        if len(set(password[i:i + length])) == 1:
            return True
    return False
