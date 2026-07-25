"""
Unit tests for password policy enforcement.
"""

import pytest

from backend.security.password_policy import (
    validate_password_strength,
    hash_for_history,
    check_password_history,
)


class TestPasswordStrength:
    def test_strong_password_passes(self):
        is_valid, violations = validate_password_strength(
            "Str0ng!Pass#2026"
        )
        assert is_valid is True
        assert violations == []

    def test_too_short(self):
        is_valid, violations = validate_password_strength("Ab1!")
        assert is_valid is False
        assert any("at least 12" in v for v in violations)

    def test_no_uppercase(self):
        is_valid, violations = validate_password_strength(
            "lowercase123!@#abc"
        )
        assert is_valid is False
        assert any("uppercase" in v for v in violations)

    def test_no_lowercase(self):
        is_valid, violations = validate_password_strength(
            "UPPERCASE123!@#ABC"
        )
        assert is_valid is False
        assert any("lowercase" in v for v in violations)

    def test_no_digit(self):
        is_valid, violations = validate_password_strength(
            "NoDigitsHere!@#"
        )
        assert is_valid is False
        assert any("digit" in v for v in violations)

    def test_no_special_char(self):
        is_valid, violations = validate_password_strength(
            "NoSpecial12345Ab"
        )
        assert is_valid is False
        assert any("special" in v for v in violations)

    def test_contains_username(self):
        is_valid, violations = validate_password_strength(
            "Str0ng!admin#2026", username="admin"
        )
        assert is_valid is False
        assert any("username" in v for v in violations)

    def test_common_password_rejected(self):
        is_valid, violations = validate_password_strength(
            "password"
        )
        assert is_valid is False
        assert any("common" in v for v in violations)

    def test_sequential_chars_rejected(self):
        is_valid, violations = validate_password_strength(
            "Abcd!@#$1234Efgh"
        )
        assert is_valid is False
        assert any("sequential" in v for v in violations)

    def test_repeated_chars_rejected(self):
        is_valid, violations = validate_password_strength(
            "Paaaassword!123"
        )
        assert is_valid is False
        assert any("repeated" in v for v in violations)


class TestPasswordHistory:
    def test_new_password_allowed(self):
        history = [
            hash_for_history("OldPassword!1"),
            hash_for_history("OldPassword!2"),
        ]
        assert check_password_history("NewStr0ng!Pass", history) is True

    def test_reused_password_rejected(self):
        old_pw = "OldPassword!1"
        history = [hash_for_history(old_pw)]
        assert check_password_history(old_pw, history) is False

    def test_empty_history_allows_any(self):
        assert check_password_history("AnyPass!123", []) is True
