# app/api/v1/endpoints/auth.py

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.rate_limit import conditional_rate_limit
from app.api.deps import get_session
from app.crud import user as crud_user
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.core.logging import get_logger, audit
from datetime import timedelta, datetime
from app.schemas.token import Token

ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()
logger = get_logger(__name__)


@router.post("/login")
@conditional_rate_limit("5/minute")  # 5 login attempts per minute
async def login(
    request: Request,
    *,
    db: AsyncSession = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """User login with audit logging"""

    # Get client information for audit logging
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")

    logger.info(
        f"Login attempt for user: {form_data.username}",
        extra={
            "event_type": "authentication",
            "email": form_data.username,
            "client_ip": client_ip,
            "user_agent": user_agent,
        },
    )

    # Get user from database
    user = await crud_user.user.get_by_email(db, email=form_data.username)

    # Check credentials
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failed authentication
        audit.log_auth_attempt(
            user_email=form_data.username,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        logger.warning(
            f"Failed login attempt for user: {form_data.username}",
            extra={
                "event_type": "authentication",
                "event_category": "failed_login",
                "email": form_data.username,
                "client_ip": client_ip,
                "reason": "invalid_credentials",
            },
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        # Log inactive user login attempt
        audit.log_auth_attempt(
            user_email=form_data.username,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        audit.log_security_event(
            "inactive_user_login_attempt",
            f"Inactive user {form_data.username} attempted to login",
            severity="medium",
            details={
                "user_email": form_data.username,
                "client_ip": client_ip,
                "user_agent": user_agent,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Update user's last login
    await crud_user.user.update(db, db_obj=user, obj_in={"last_login": datetime.now()})

    # Log successful authentication
    audit.log_auth_attempt(
        user_email=user.email, success=True, ip_address=client_ip, user_agent=user_agent
    )

    audit.log_user_action(
        user_id=str(user.id),
        action="login",
        details={
            "client_ip": client_ip,
            "user_agent": user_agent,
            "token_expires": access_token_expires.total_seconds(),
        },
    )

    logger.info(
        f"Successful login for user: {user.email}",
        extra={
            "event_type": "authentication",
            "event_category": "successful_login",
            "user_id": str(user.id),
            "email": user.email,
            "client_ip": client_ip,
        },
    )

    return Token(access_token=access_token, token_type="bearer")
