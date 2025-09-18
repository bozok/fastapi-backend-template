from typing import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import async_session
from sqlmodel import SQLModel, Field
from fastapi import Query
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import InvalidTokenError as JWTError
from app.core.security import SECRET_KEY, ALGORITHM
from app.core.logging import get_logger, audit
from app.schemas.token import TokenData
from app.crud import user as crud_user
from app.models.user import User


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


# --- Authentication Dependencies ---

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", scheme_name="JWT")

logger = get_logger(__name__)


async def get_current_user(
    db: AsyncSession = Depends(get_session), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    This dependency:
    1. Extracts the JWT token from the Authorization header
    2. Validates and decodes the token
    3. Retrieves the user from the database
    4. Logs authentication events for audit
    5. Returns the authenticated User object

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            logger.warning(
                "JWT token missing 'sub' field",
                extra={
                    "event_type": "authentication",
                    "event_category": "invalid_token",
                    "reason": "missing_subject",
                },
            )
            raise credentials_exception

        token_data = TokenData(email=email)

    except JWTError as e:
        logger.warning(
            f"JWT token validation failed: {str(e)}",
            extra={
                "event_type": "authentication",
                "event_category": "invalid_token",
                "reason": "jwt_decode_error",
                "error": str(e),
            },
        )

        # Log security event for invalid token
        audit.log_security_event(
            "invalid_jwt_token",
            f"Failed to decode JWT token: {str(e)}",
            severity="medium",
            details={"error": str(e)},
        )

        raise credentials_exception

    # Get user from database
    user = await crud_user.user.get_by_email(db, email=token_data.email)

    if user is None:
        logger.warning(
            f"User not found for email: {token_data.email}",
            extra={
                "event_type": "authentication",
                "event_category": "user_not_found",
                "email": token_data.email,
            },
        )

        # Log security event for non-existent user
        audit.log_security_event(
            "authentication_nonexistent_user",
            f"Token valid but user not found: {token_data.email}",
            severity="high",
            details={"email": token_data.email},
        )

        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        logger.warning(
            f"Inactive user attempted access: {user.email}",
            extra={
                "event_type": "authentication",
                "event_category": "inactive_user_access",
                "user_id": str(user.id),
                "email": user.email,
            },
        )

        # Log security event for inactive user
        audit.log_security_event(
            "inactive_user_access_attempt",
            f"Inactive user attempted to access protected resource: {user.email}",
            severity="medium",
            details={"user_id": str(user.id), "email": user.email},
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive"
        )

    # Log successful authentication for audit
    logger.debug(
        f"User authenticated successfully: {user.email}",
        extra={
            "event_type": "authentication",
            "event_category": "successful_auth",
            "user_id": str(user.id),
            "email": user.email,
        },
    )

    # Log data access
    audit.log_data_access(
        user_id=str(user.id),
        resource_type="user_authentication",
        resource_id=str(user.id),
        operation="token_validation",
    )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current active user.

    This is a convenience dependency that combines get_current_user
    with an additional active check. Use this when you want to be
    extra explicit about requiring an active user.

    Note: get_current_user already checks is_active, so this is
    mainly for semantic clarity.
    """
    return current_user


# Optional: Admin user dependency
async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current user and verify admin privileges.

    Use this dependency for admin-only endpoints.
    """
    if not getattr(current_user, "is_superuser", False):
        logger.warning(
            f"Non-admin user attempted admin access: {current_user.email}",
            extra={
                "event_type": "authorization",
                "event_category": "admin_access_denied",
                "user_id": str(current_user.id),
                "email": current_user.email,
            },
        )

        # Log security event for unauthorized admin access
        audit.log_security_event(
            "unauthorized_admin_access",
            f"Non-admin user attempted admin access: {current_user.email}",
            severity="high",
            details={"user_id": str(current_user.id), "email": current_user.email},
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )

    return current_user


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
