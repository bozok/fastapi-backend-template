# app/schemas/response.py
from typing import Generic, List, Optional, TypeVar

from sqlmodel import SQLModel, Field

# Define a TypeVar for generic data types
DataT = TypeVar("DataT")


class MessageResponse(SQLModel):
    """Standard response for operations that only return a message."""

    status: str = "success"
    message: str


class StandardResponse(SQLModel):
    """Standard response for operations with optional data."""

    success: bool = True
    message: str
    data: Optional[dict] = None


class SingleResponse(SQLModel, Generic[DataT]):
    """Standard wrapper for single object responses."""

    status: str = "success"
    message: Optional[str] = None
    data: DataT


class PaginationMeta(SQLModel):
    """Metadata for paginated responses."""

    total_items: int = Field(..., description="Total number of items available")
    total_pages: int = Field(..., description="Total number of pages")
    current_page: int = Field(..., description="Current page number (1-based)")
    limit: int = Field(..., description="Number of items per page")
    # skip: int = Field(..., description="Number of items skipped (offset)") # Optional to include skip


class PaginatedResponse(SQLModel, Generic[DataT]):
    """Standard wrapper for paginated list responses."""

    status: str = "success"
    message: Optional[str] = None
    pagination: PaginationMeta
    items: List[DataT]  # Changed 'data' to 'items' for lists, common practice
