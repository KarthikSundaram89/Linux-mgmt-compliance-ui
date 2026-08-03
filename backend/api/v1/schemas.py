"""
API Schemas
===========

Pydantic models for request/response serialization.
Shared pagination and filtering schemas.
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ─── Pagination ────────────────────────────────────────────────────

class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=25, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")
    search: Optional[str] = Field(default=None, description="Search query")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: List[Any] = Field(description="Page items")
    total: int = Field(description="Total item count")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")


# ─── Server Schemas ───────────────────────────────────────────────

class ServerCreate(BaseModel):
    """Schema for creating a new server."""
    hostname: str = Field(..., max_length=255)
    ip_address: str = Field(..., max_length=45)
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    description: Optional[str] = None
    environment: str = Field(default="production", max_length=50)
    location: Optional[str] = Field(default=None, max_length=100)
    credential_profile_id: str = Field(...)
    tags: Optional[str] = None


class ServerUpdate(BaseModel):
    """Schema for updating a server."""
    hostname: Optional[str] = Field(default=None, max_length=255)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    description: Optional[str] = None
    environment: Optional[str] = Field(default=None, max_length=50)
    location: Optional[str] = None
    credential_profile_id: Optional[str] = None
    is_active: Optional[bool] = None
    tags: Optional[str] = None


class ServerResponse(BaseModel):
    """Schema for server API responses."""
    id: str
    hostname: str
    ip_address: str
    port: Optional[int]
    description: Optional[str]
    environment: str
    location: Optional[str]
    os_family: Optional[str]
    os_version: Optional[str]
    credential_profile_id: str
    is_active: bool
    last_collection_at: Optional[datetime]
    last_collection_status: Optional[str]
    tags: Optional[str]
    # AWS CMDB fields
    aws_region: Optional[str] = None
    aws_account_name: Optional[str] = None
    instance_id: Optional[str] = None
    app_name: Optional[str] = None
    pdo: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Credential Profile Schemas ────────────────────────────────────

class CredentialProfileCreate(BaseModel):
    """Schema for creating a credential profile."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    ssh_username: str = Field(..., max_length=100)
    ssh_port: int = Field(default=22, ge=1, le=65535)
    secret_arn: str = Field(..., max_length=512)
    passphrase_secret_arn: Optional[str] = Field(default=None, max_length=512)
    connection_timeout: int = Field(default=30, ge=5, le=300)
    command_timeout: int = Field(default=60, ge=10, le=600)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=5, ge=1, le=60)


class CredentialProfileResponse(BaseModel):
    """Schema for credential profile API responses."""
    id: str
    name: str
    description: Optional[str]
    ssh_username: str
    ssh_port: int
    connection_timeout: int
    command_timeout: int
    max_retries: int
    retry_delay_seconds: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    server_count: Optional[int] = None

    class Config:
        from_attributes = True


# ─── Collection Schemas ────────────────────────────────────────────

class CollectionResponse(BaseModel):
    """Schema for collection API responses."""
    id: str
    server_id: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    error_message: Optional[str]
    retry_count: int
    triggered_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Change History Schemas ────────────────────────────────────────

class ChangeResponse(BaseModel):
    """Schema for change history API responses."""
    id: str
    server_id: str
    category: str
    change_type: str
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    severity: str
    detected_at: datetime
    acknowledged: bool
    acknowledged_by: Optional[str]

    class Config:
        from_attributes = True


# ─── Auth Schemas ──────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Login request body."""
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class TokenRefreshRequest(BaseModel):
    """Token refresh request body."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request body."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ─── Dashboard Schemas ─────────────────────────────────────────────

class DashboardStats(BaseModel):
    """Dashboard summary statistics."""
    total_servers: int
    active_servers: int
    servers_online: int
    servers_failed: int
    total_collections_today: int
    total_changes_today: int
    critical_changes: int
    pending_notifications: int


# ─── Notification Schemas ──────────────────────────────────────────

class NotificationResponse(BaseModel):
    """Schema for notification API responses."""
    id: str
    title: str
    message: str
    severity: str
    category: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
