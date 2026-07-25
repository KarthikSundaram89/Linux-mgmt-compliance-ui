"""
Base Repository
===============

Generic repository providing common CRUD operations.
All specific repositories inherit from this base class.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository with common CRUD operations.
    
    Type Parameters:
        ModelType: The SQLAlchemy model class this repository manages.
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self._model = model
        self._session = session
    
    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """Retrieve a single record by its primary key."""
        result = await self._session.execute(
            select(self._model).where(self._model.id == id)
        )
        return result.scalar_one_or_none()


    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
    ) -> List[ModelType]:
        """
        Retrieve multiple records with pagination and filtering.
        
        Args:
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.
            filters: Dictionary of field_name: value filters.
            order_by: Column name to sort by.
            descending: Sort in descending order if True.
        
        Returns:
            List of matching model instances.
        """
        query = select(self._model)
        
        # Apply filters
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self._model, field):
                    column = getattr(self._model, field)
                    if isinstance(value, str) and "%" in value:
                        conditions.append(column.ilike(value))
                    else:
                        conditions.append(column == value)
            if conditions:
                query = query.where(and_(*conditions))
        
        # Apply ordering
        if order_by and hasattr(self._model, order_by):
            column = getattr(self._model, order_by)
            query = query.order_by(
                column.desc() if descending else column.asc()
            )
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self._session.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count records matching the given filters."""
        query = select(func.count()).select_from(self._model)
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self._model, field):
                    column = getattr(self._model, field)
                    conditions.append(column == value)
            if conditions:
                query = query.where(and_(*conditions))
        result = await self._session.execute(query)
        return result.scalar() or 0
    
    async def create(self, obj: ModelType) -> ModelType:
        """Insert a new record into the database."""
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj
    
    async def update(
        self, obj: ModelType, data: Dict[str, Any]
    ) -> ModelType:
        """Update an existing record with the provided data."""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj
    
    async def delete(self, obj: ModelType) -> None:
        """Permanently delete a record."""
        await self._session.delete(obj)
        await self._session.flush()
    
    async def soft_delete(self, obj: ModelType) -> ModelType:
        """Mark a record as deleted without removing it."""
        from datetime import datetime, timezone
        obj.is_deleted = True
        obj.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        return obj
