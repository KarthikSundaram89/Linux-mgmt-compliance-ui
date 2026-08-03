"""
Application Configuration
=========================

Centralized configuration using Pydantic BaseSettings.
All configuration is driven by environment variables with sensible defaults.
Supports .env files for local development.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All sensitive values should be provided via environment variables
    or a .env file. Never hardcode secrets.
    """
    
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ─── Application ───────────────────────────────────────────────
    app_name: str = "Linux Inventory Manager"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", description="deployment environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # ─── Server ────────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0", description="Server bind address")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of worker processes")
    
    # ─── Security ──────────────────────────────────────────────────
    secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-USE-STRONG-RANDOM-KEY",
        description="Secret key for JWT signing and encryption",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_expiration_minutes: int = Field(default=480, description="JWT token expiration in minutes")
    jwt_refresh_expiration_days: int = Field(default=7, description="Refresh token expiration in days")
    
    # ─── CORS ──────────────────────────────────────────────────────
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )
    allowed_hosts: List[str] = Field(
        default=[],
        description="Allowed host headers (empty = all)",
    )
    
    # ─── Database ──────────────────────────────────────────────────
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{BASE_DIR}/storage/inventory.db",
        description="Database connection URL",
    )
    database_echo: bool = Field(default=False, description="Echo SQL statements")
    database_pool_size: int = Field(default=20, description="Connection pool size")
    database_max_overflow: int = Field(default=10, description="Max pool overflow")
    
    # ─── SSH ───────────────────────────────────────────────────────
    ssh_connection_timeout: int = Field(default=30, description="SSH connection timeout (seconds)")
    ssh_command_timeout: int = Field(default=60, description="SSH command timeout (seconds)")
    ssh_max_pool_size: int = Field(default=50, description="Maximum SSH connections in pool")
    ssh_idle_timeout: int = Field(default=300, description="Idle connection cleanup (seconds)")
    ssh_max_retries: int = Field(default=3, description="SSH connection retry attempts")
    ssh_retry_delay: int = Field(default=5, description="Delay between SSH retries (seconds)")
    
    # ─── Scheduler ─────────────────────────────────────────────────
    scheduler_enabled: bool = Field(default=True, description="Enable collection scheduler")
    scheduler_collection_hour: int = Field(default=2, description="Daily collection hour (0-23)")
    scheduler_collection_minute: int = Field(default=0, description="Daily collection minute (0-59)")
    scheduler_retry_interval_minutes: int = Field(default=60, description="Retry interval for failed collections")
    scheduler_max_concurrent_collections: int = Field(
        default=20,
        description="Maximum concurrent SSH collection sessions",
    )
    
    # ─── Secrets ───────────────────────────────────────────────────
    secrets_provider: str = Field(
        default="aws_secrets_manager",
        description="Secrets provider (aws_secrets_manager, vault, local)",
    )
    aws_region: str = Field(default="us-east-1", description="AWS region for Secrets Manager")
    aws_profile: Optional[str] = Field(default=None, description="AWS CLI profile name")
    
    # ─── Storage ───────────────────────────────────────────────────
    storage_base_path: Path = Field(
        default=BASE_DIR / "storage",
        description="Base path for file storage",
    )
    snapshots_path: Path = Field(
        default=BASE_DIR / "storage" / "snapshots",
        description="Path for inventory snapshots",
    )
    reports_path: Path = Field(
        default=BASE_DIR / "storage" / "reports",
        description="Path for generated reports",
    )
    exports_path: Path = Field(
        default=BASE_DIR / "storage" / "exports",
        description="Path for data exports",
    )
    
    # ─── Logging ───────────────────────────────────────────────────
    log_level: str = Field(default="INFO", description="Application log level")
    log_dir: Path = Field(default=BASE_DIR / "logs", description="Log file directory")
    log_max_size_mb: int = Field(default=50, description="Max log file size in MB")
    log_backup_count: int = Field(default=10, description="Number of rotated log files to keep")
    log_format: str = Field(default="json", description="Log format (json or text)")
    
    # ─── Notifications ─────────────────────────────────────────────
    smtp_host: Optional[str] = Field(default=None, description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password_secret_arn: Optional[str] = Field(
        default=None,
        description="AWS Secrets Manager ARN for SMTP password",
    )
    smtp_from_address: str = Field(
        default="linux-inventory@company.com",
        description="Email from address",
    )
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    
    # ─── Reports ───────────────────────────────────────────────────
    report_retention_days: int = Field(default=90, description="Days to retain generated reports")
    snapshot_retention_days: int = Field(default=365, description="Days to retain snapshots")
    
    # ─── CMDB Import (EFS-mounted CSV) ─────────────────────────────
    cmdb_import_enabled: bool = Field(
        default=True, description="Enable automatic CMDB CSV import"
    )
    cmdb_import_path: str = Field(
        default="/mnt/efs/cmdb/ec2_inventory.csv",
        description="Path to the CMDB CSV file on EFS mount",
    )
    cmdb_import_schedule_hour: int = Field(
        default=1, description="Hour to run CMDB import (0-23, before collection)"
    )
    cmdb_import_schedule_minute: int = Field(
        default=0, description="Minute to run CMDB import"
    )
    cmdb_csv_delimiter: str = Field(
        default=",", description="CSV delimiter character"
    )
    cmdb_csv_encoding: str = Field(
        default="utf-8", description="CSV file encoding"
    )
    cmdb_csv_has_header: bool = Field(
        default=True, description="Whether the CSV file has a header row"
    )
    # Column mapping: which CSV column maps to which server field
    cmdb_col_region: str = Field(
        default="region", description="CSV column name for AWS region"
    )
    cmdb_col_account_name: str = Field(
        default="account_name", description="CSV column name for AWS account/profile"
    )
    cmdb_col_instance_id: str = Field(
        default="instance_id", description="CSV column name for EC2 instance ID"
    )
    cmdb_col_instance_ip: str = Field(
        default="instance_ip", description="CSV column name for instance IP address"
    )
    cmdb_col_name: str = Field(
        default="Name", description="CSV column name for server name tag (used as hostname)"
    )
    cmdb_col_app_name: str = Field(
        default="app_name", description="CSV column name for application name tag"
    )
    cmdb_col_pdo: str = Field(
        default="PDO", description="CSV column name for PDO tag"
    )
    cmdb_default_credential_profile: str = Field(
        default="", description="Default credential profile ID for newly imported servers"
    )
    cmdb_default_ssh_port: int = Field(
        default=22, description="Default SSH port for imported servers"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a recognized Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return upper_v
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is recognized."""
        valid_envs = {"development", "staging", "production", "testing"}
        if v.lower() not in valid_envs:
            raise ValueError(f"Invalid environment: {v}. Must be one of {valid_envs}")
        return v.lower()


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses lru_cache to ensure settings are loaded only once
    and reused across the application lifecycle.
    
    Returns:
        Settings: Application settings instance.
    """
    return Settings()
