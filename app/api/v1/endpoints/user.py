import uuid
import math
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.rate_limit import limiter, RateLimitTiers

from app.api.deps import (
    get_pagination_params,
    get_session,
    get_current_user,
    PaginationParams,
)
from app.crud import user as crud_user
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.schemas.response import SingleResponse, PaginatedResponse, PaginationMeta

from app.services.user import user_service

router = APIRouter()


@router.post("/", response_model=SingleResponse[UserRead])
@limiter.limit(RateLimitTiers.PUBLIC_READ)
@limiter.limit(RateLimitTiers.BURST_PROTECTION)
async def create_user(
    request: Request,
    *,
    db: AsyncSession = Depends(get_session),
    user_in: UserCreate,
) -> SingleResponse[UserRead]:
    """Public endpoint for user registration"""
    created_user = await user_service.create_user(db, user_in=user_in)
    return SingleResponse(data=UserRead.model_validate(created_user))


@router.get("/me", response_model=SingleResponse[UserRead])
async def get_my_profile(
    request: Request, *, current_user: User = Depends(get_current_user)
) -> SingleResponse[UserRead]:
    """Get current user's profile (authenticated endpoint)"""
    return SingleResponse(data=UserRead.model_validate(current_user))


@router.get("/{user_id}", response_model=SingleResponse[UserRead])
@limiter.limit(RateLimitTiers.PUBLIC_READ)
@limiter.limit(RateLimitTiers.BURST_PROTECTION)
async def read_user(
    request: Request,
    user_id: uuid.UUID,
    *,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SingleResponse[UserRead]:
    """Get any user's profile (authenticated endpoint)"""
    user = await crud_user.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return SingleResponse(data=UserRead.model_validate(user))


@router.get("/", response_model=PaginatedResponse[UserRead])
@limiter.limit(RateLimitTiers.PUBLIC_READ)
@limiter.limit(RateLimitTiers.BURST_PROTECTION)
async def read_users(
    request: Request,
    *,
    pagination: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_session),
    current_admin: User = Depends(get_current_user),
) -> PaginatedResponse[UserRead]:
    """Get all users (admin only endpoint)"""
    users = await crud_user.user.get_multi(
        db, skip=pagination.skip, limit=pagination.limit
    )
    total_rows = await crud_user.user.get_count(db)

    total_pages = (
        math.ceil(total_rows / pagination.limit) if pagination.limit > 0 else 0
    )
    current_page = (
        (pagination.skip // pagination.limit) + 1 if pagination.limit > 0 else 1
    )

    pagination_meta = PaginationMeta(
        total_items=total_rows,
        total_pages=total_pages,
        current_page=current_page,
        limit=pagination.limit,
    )

    user_reads = [UserRead.model_validate(user) for user in users]

    return PaginatedResponse(items=user_reads, pagination=pagination_meta)
