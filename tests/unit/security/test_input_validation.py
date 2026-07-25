"""
Unit tests for input validation and sanitization.
"""

import pytest

from backend.security.input_validation import (
    validate_hostname,
    validate_ip_address,
    validate_username,
    validate_uuid,
    validate_sort_field,
    sanitize_string,
    validate_pagination,
)


class TestHostnameValidation:
    def test_valid_hostname(self):
        assert validate_hostname("web-server-01") == "web-server-01"
        assert validate_hostname("db.prod.internal") == "db.prod.internal"
        assert validate_hostname("a") == "a"

    def test_invalid_hostname_chars(self):
        with pytest.raises(ValueError):
            validate_hostname("server;rm -rf /")

    def test_invalid_hostname_too_long(self):
        with pytest.raises(ValueError):
            validate_hostname("a" * 256)

    def test_invalid_hostname_starts_with_dash(self):
        with pytest.raises(ValueError):
            validate_hostname("-invalid")


class TestIPValidation:
    def test_valid_ipv4(self):
        assert validate_ip_address("192.168.1.1") == "192.168.1.1"
        assert validate_ip_address("10.0.0.1") == "10.0.0.1"
        assert validate_ip_address("255.255.255.255") == "255.255.255.255"

    def test_invalid_ip(self):
        with pytest.raises(ValueError):
            validate_ip_address("999.999.999.999")
        with pytest.raises(ValueError):
            validate_ip_address("not-an-ip")
        with pytest.raises(ValueError):
            validate_ip_address("192.168.1.1; cat /etc/passwd")


class TestUsernameValidation:
    def test_valid_username(self):
        assert validate_username("admin") == "admin"
        assert validate_username("john.doe") == "john.doe"
        assert validate_username("user_123") == "user_123"

    def test_invalid_username_starts_with_number(self):
        with pytest.raises(ValueError):
            validate_username("123user")

    def test_invalid_username_special_chars(self):
        with pytest.raises(ValueError):
            validate_username("user;drop table")
        with pytest.raises(ValueError):
            validate_username("user<script>")

    def test_invalid_username_too_short(self):
        with pytest.raises(ValueError):
            validate_username("ab")


class TestUUIDValidation:
    def test_valid_uuid(self):
        validate_uuid("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

    def test_invalid_uuid(self):
        with pytest.raises(ValueError):
            validate_uuid("not-a-uuid")
        with pytest.raises(ValueError):
            validate_uuid("' OR 1=1 --")


class TestSortFieldValidation:
    def test_valid_sort_field(self):
        assert validate_sort_field("hostname") == "hostname"
        assert validate_sort_field("created_at") == "created_at"

    def test_invalid_sort_field_injection(self):
        with pytest.raises(ValueError):
            validate_sort_field("hostname; DROP TABLE servers")
        with pytest.raises(ValueError):
            validate_sort_field("1=1")
        with pytest.raises(ValueError):
            validate_sort_field("nonexistent_field")


class TestSanitizeString:
    def test_strips_whitespace(self):
        assert sanitize_string("  hello  ") == "hello"

    def test_truncates_long_strings(self):
        result = sanitize_string("a" * 1000, max_length=100)
        assert len(result) == 100

    def test_rejects_script_tags(self):
        with pytest.raises(ValueError):
            sanitize_string("<script>alert('xss')</script>")

    def test_rejects_event_handlers(self):
        with pytest.raises(ValueError):
            sanitize_string('onerror="alert(1)"')

    def test_rejects_javascript_protocol(self):
        with pytest.raises(ValueError):
            sanitize_string("javascript:alert(1)")

    def test_allows_normal_strings(self):
        assert sanitize_string("Hello World") == "Hello World"
        assert sanitize_string("server-01.prod") == "server-01.prod"


class TestPagination:
    def test_valid_pagination(self):
        assert validate_pagination(1, 25) == (1, 25)
        assert validate_pagination(5, 100) == (5, 100)

    def test_invalid_page_zero(self):
        with pytest.raises(ValueError):
            validate_pagination(0, 25)

    def test_invalid_page_size_too_large(self):
        with pytest.raises(ValueError):
            validate_pagination(1, 500)

    def test_invalid_page_size_zero(self):
        with pytest.raises(ValueError):
            validate_pagination(1, 0)
