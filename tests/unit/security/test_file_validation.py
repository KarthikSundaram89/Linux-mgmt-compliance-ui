"""
Unit tests for file upload and CSV import validation.
"""

import pytest

from backend.security.file_validation import (
    validate_file_upload,
    generate_safe_filename,
    validate_csv_import,
    sanitize_csv_value,
)


class TestFileUploadValidation:
    def test_valid_csv_upload(self):
        valid, error = validate_file_upload(
            "servers.csv", "text/csv", 1024
        )
        assert valid is True
        assert error is None

    def test_reject_executable(self):
        valid, error = validate_file_upload(
            "payload.exe", "application/x-msdownload", 1024
        )
        assert valid is False
        assert "not allowed" in error

    def test_reject_oversized_file(self):
        valid, error = validate_file_upload(
            "big.csv", "text/csv", 100 * 1024 * 1024
        )
        assert valid is False
        assert "too large" in error.lower()

    def test_reject_directory_traversal(self):
        valid, error = validate_file_upload(
            "../../etc/passwd", "text/plain", 100
        )
        assert valid is False
        assert "traversal" in error.lower()

    def test_reject_path_separator(self):
        valid, error = validate_file_upload(
            "/etc/shadow", "text/plain", 100
        )
        assert valid is False


class TestSafeFilename:
    def test_generates_random_name(self):
        name = generate_safe_filename("original.csv")
        assert name.endswith(".csv")
        assert name != "original.csv"
        assert len(name) > 10

    def test_preserves_valid_extension(self):
        assert generate_safe_filename("data.json").endswith(".json")
        assert generate_safe_filename("import.txt").endswith(".txt")

    def test_rejects_bad_extension(self):
        name = generate_safe_filename("payload.exe")
        assert name.endswith(".dat")


class TestCSVImport:
    def test_valid_csv(self):
        content = b"hostname,ip_address\nserver1,10.0.0.1\nserver2,10.0.0.2\n"
        valid, error, rows = validate_csv_import(content)
        assert valid is True
        assert error is None
        assert len(rows) == 2
        assert rows[0]["hostname"] == "server1"

    def test_required_headers_missing(self):
        content = b"name,ip\nserver1,10.0.0.1\n"
        valid, error, _ = validate_csv_import(
            content, required_headers=["hostname", "ip_address"]
        )
        assert valid is False
        assert "Missing required" in error

    def test_csv_injection_sanitized(self):
        content = b"hostname,command\nserver1,=CMD('calc')\n"
        valid, error, rows = validate_csv_import(content)
        assert valid is True
        # Injection prefix should be escaped
        assert rows[0]["command"].startswith("'")

    def test_empty_csv_rejected(self):
        content = b""
        valid, error, _ = validate_csv_import(content)
        assert valid is False

    def test_oversized_csv_rejected(self):
        content = b"col\n" + b"x" * (11 * 1024 * 1024)
        valid, error, _ = validate_csv_import(content)
        assert valid is False
        assert "too large" in error.lower()


class TestCSVSanitization:
    def test_normal_value_unchanged(self):
        assert sanitize_csv_value("hello world") == "hello world"

    def test_formula_injection_escaped(self):
        assert sanitize_csv_value("=1+1").startswith("'")
        assert sanitize_csv_value("+1+1").startswith("'")
        assert sanitize_csv_value("-1+1").startswith("'")
        assert sanitize_csv_value("@SUM(A1)").startswith("'")

    def test_null_bytes_removed(self):
        assert "\x00" not in sanitize_csv_value("test\x00value")
