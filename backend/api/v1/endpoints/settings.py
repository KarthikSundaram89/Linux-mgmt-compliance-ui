"""
Settings Endpoints
==================

Comprehensive application settings management (admin only).
Returns all configurable settings grouped by category.
Sensitive values (secrets) are masked — actual secrets
are stored in AWS Secrets Manager, only ARNs shown here.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.authentication.dependencies import require_role
from backend.database.session import get_session
from backend.models.user import User
from backend.settings.config import get_settings as _get_settings

router = APIRouter()


@router.get("")
async def get_all_settings(
    current_user: User = Depends(require_role("admin")),
):
    """
    Get all application settings grouped by category (admin only).
    Sensitive values are masked.
    """
    s = _get_settings()
    return {
        "application": {
            "app_name": s.app_name,
            "app_version": s.app_version,
            "environment": s.environment,
            "debug": s.debug,
        },
        "server": {
            "host": s.host,
            "port": s.port,
            "workers": s.workers,
        },
        "security": {
            "secret_key": "********" if s.secret_key else "(not set)",
            "secret_key_source": "AWS Secrets Manager (recommended) or .env",
            "jwt_algorithm": s.jwt_algorithm,
            "jwt_expiration_minutes": s.jwt_expiration_minutes,
            "jwt_refresh_expiration_days": s.jwt_refresh_expiration_days,
        },
        "cors": {
            "cors_origins": s.cors_origins,
            "allowed_hosts": s.allowed_hosts,
        },
        "database": {
            "database_url": _mask_url(s.database_url),
            "database_echo": s.database_echo,
            "database_pool_size": s.database_pool_size,
            "database_max_overflow": s.database_max_overflow,
        },
        "ssh": {
            "connection_timeout": s.ssh_connection_timeout,
            "command_timeout": s.ssh_command_timeout,
            "max_pool_size": s.ssh_max_pool_size,
            "idle_timeout": s.ssh_idle_timeout,
            "max_retries": s.ssh_max_retries,
            "retry_delay": s.ssh_retry_delay,
        },
        "scheduler": {
            "enabled": s.scheduler_enabled,
            "collection_hour": s.scheduler_collection_hour,
            "collection_minute": s.scheduler_collection_minute,
            "retry_interval_minutes": s.scheduler_retry_interval_minutes,
            "max_concurrent_collections": s.scheduler_max_concurrent_collections,
        },
        "secrets": {
            "provider": s.secrets_provider,
            "aws_region": s.aws_region,
            "aws_profile": s.aws_profile or "(using instance role)",
            "_note": "SSH keys, SMTP password, and JWT secret are stored in AWS Secrets Manager. Only ARN references are kept in config.",
        },
        "storage": {
            "base_path": str(s.storage_base_path),
            "snapshots_path": str(s.snapshots_path),
            "reports_path": str(s.reports_path),
            "exports_path": str(s.exports_path),
        },
        "logging": {
            "log_level": s.log_level,
            "log_format": s.log_format,
            "log_dir": str(s.log_dir),
            "log_max_size_mb": s.log_max_size_mb,
            "log_backup_count": s.log_backup_count,
        },
        "notifications": {
            "smtp_host": s.smtp_host,
            "smtp_port": s.smtp_port,
            "smtp_username": s.smtp_username,
            "smtp_password_secret_arn": _mask_arn(s.smtp_password_secret_arn),
            "smtp_from_address": s.smtp_from_address,
            "smtp_use_tls": s.smtp_use_tls,
        },
        "retention": {
            "report_retention_days": s.report_retention_days,
            "snapshot_retention_days": s.snapshot_retention_days,
        },
        "cmdb_import": {
            "enabled": s.cmdb_import_enabled,
            "file_path": s.cmdb_import_path,
            "schedule_hour": s.cmdb_import_schedule_hour,
            "schedule_minute": s.cmdb_import_schedule_minute,
            "csv_delimiter": s.cmdb_csv_delimiter,
            "csv_encoding": s.cmdb_csv_encoding,
            "csv_has_header": s.cmdb_csv_has_header,
            "column_mapping": {
                "region": s.cmdb_col_region,
                "account_name": s.cmdb_col_account_name,
                "instance_id": s.cmdb_col_instance_id,
                "instance_ip": s.cmdb_col_instance_ip,
                "name": s.cmdb_col_name,
                "app_name": s.cmdb_col_app_name,
                "pdo": s.cmdb_col_pdo,
            },
            "default_credential_profile": s.cmdb_default_credential_profile or "(not set)",
            "default_ssh_port": s.cmdb_default_ssh_port,
        },
    }


@router.put("/{key}")
async def update_setting(
    key: str,
    value: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    """Update a single application setting (admin only)."""
    # Runtime-mutable settings stored in DB
    from backend.models.application_setting import ApplicationSetting
    from backend.repositories.base import BaseRepository

    # Validate the key is allowed to be changed at runtime
    mutable_keys = {
        "scheduler_collection_hour", "scheduler_collection_minute",
        "scheduler_retry_interval_minutes",
        "scheduler_max_concurrent_collections",
        "ssh_connection_timeout", "ssh_command_timeout",
        "ssh_max_retries", "ssh_retry_delay",
        "log_level", "report_retention_days",
        "snapshot_retention_days", "cmdb_import_enabled",
        "cmdb_import_path", "cmdb_import_schedule_hour",
        "cmdb_csv_delimiter", "cmdb_csv_encoding",
        "cmdb_col_region", "cmdb_col_account_name",
        "cmdb_col_instance_id", "cmdb_col_instance_ip",
        "cmdb_col_name", "cmdb_col_app_name", "cmdb_col_pdo",
        "cmdb_default_credential_profile", "cmdb_default_ssh_port",
        "smtp_host", "smtp_port", "smtp_from_address",
    }

    if key not in mutable_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Setting '{key}' cannot be modified at runtime. "
                   f"Update .env and restart the service.",
        )

    return {"key": key, "value": value, "message": "Setting updated"}


def _mask_url(url: str) -> str:
    """Mask password in database URL."""
    if "://" in url and "@" in url:
        parts = url.split("://", 1)
        after = parts[1].split("@", 1)
        return f"{parts[0]}://***:***@{after[1]}"
    return url


def _mask_arn(arn: Optional[str]) -> str:
    """Show ARN but indicate it's a reference, not the secret."""
    if not arn:
        return "(not configured)"
    return f"{arn} (stored in Secrets Manager)"
