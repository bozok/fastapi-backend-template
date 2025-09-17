from typing import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import async_session
from sqlmodel import SQLModel, Field
from fastapi import Query


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


# --- Pagination Dependency ---
class PaginationParams(SQLModel):
    skip: int = Field(0, ge=0, description="Number of items to skip (offset)")
    limit: int = Field(
        100, ge=1, le=200, description="Number of items per page (max 200)"
    )  # Added max limit


# Dependency function using the Pydantic model
# This allows automatic validation of skip/limit by FastAPI
def get_pagination_params(
    skip: int = Query(0, ge=0, description="Number of items to skip (offset)"),
    limit: int = Query(
        100, ge=1, le=200, description="Number of items per page (max 200)"
    ),  # Added max limit
) -> PaginationParams:
    """
    Dependency to get validated pagination parameters (skip, limit).
    """
    return PaginationParams(skip=skip, limit=limit)
