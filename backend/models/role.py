"""
Role and Permission Models
==========================

RBAC (Role-Based Access Control) models.
Defines roles, permissions, and their associations.
"""

from typing import Optional, List

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, generate_uuid


class Role(Base, TimestampMixin):
    """
    A role that groups permissions and is assigned to users.
    
    Attributes:
        id: Unique role identifier (UUID).
        name: Role name (admin, operator, viewer, auditor).
        description: Human-readable role description.
    """
    
    __tablename__ = "roles"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="role", lazy="dynamic"
    )

    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission", back_populates="role", lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Role(name={self.name})>"


class Permission(Base, TimestampMixin):
    """
    A specific permission that can be assigned to a role.
    
    Attributes:
        id: Unique permission identifier (UUID).
        name: Permission name (e.g., servers.read, servers.write).
        resource: Resource this permission applies to.
        action: Action allowed (read, write, delete, execute).
        description: Human-readable description.
    """
    
    __tablename__ = "permissions"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    resource: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(
        String(20), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<Permission(name={self.name})>"


class RolePermission(Base):
    """
    Association table linking roles to permissions.
    """
    
    __tablename__ = "role_permissions"
    
    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id"),
        primary_key=True,
    )
    permission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("permissions.id"),
        primary_key=True,
    )
    
    # Relationships
    role: Mapped["Role"] = relationship(
        "Role", back_populates="role_permissions"
    )
    permission: Mapped["Permission"] = relationship(
        "Permission", lazy="selectin"
    )
