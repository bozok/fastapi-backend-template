import uuid
import math
from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.rate_limit import limiter, RateLimitTiers

from app.api.deps import get_pagination_params, get_session, PaginationParams
from app.crud import user as crud_user
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
    created_user = await user_service.create(db, user_in=user_in)
    return SingleResponse(data=UserRead.model_validate(created_user))


@router.get("/{user_id}", response_model=SingleResponse[UserRead])
@limiter.limit(RateLimitTiers.PUBLIC_READ)
@limiter.limit(RateLimitTiers.BURST_PROTECTION)
async def read_user(
    request: Request, user_id: uuid.UUID, db: AsyncSession = Depends(get_session)
) -> SingleResponse[UserRead]:
    user = await user_service.get_by_id(db, user_id=user_id)
    return SingleResponse(data=UserRead.model_validate(user))


@router.get("/", response_model=PaginatedResponse[UserRead])
@limiter.limit(RateLimitTiers.PUBLIC_READ)
@limiter.limit(RateLimitTiers.BURST_PROTECTION)
async def read_users(
    request: Request,
    pagination: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_session),
) -> PaginatedResponse[UserRead]:
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
