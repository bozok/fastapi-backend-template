# app/services/user_service.py

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import hash_password
from app.core.logging import get_logger, audit, log_performance
from app.crud.user import user as crud_user
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

logger = get_logger(__name__)


class UserService:
    @log_performance("user_service.create_user")
    async def create_user(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        """
        Handles the business logic for creating a user, including validation,
        password hashing, and audit logging.
        """
        logger.info(
            f"Creating new user: {user_in.email}",
            extra={
                "event_type": "user_management",
                "action": "create_user",
                "email": user_in.email,
            },
        )

        # 1. Validate Email Existence
        existing_user = await crud_user.get_by_email(db, email=user_in.email)
        if existing_user:
            logger.warning(
                f"User creation failed - email already exists: {user_in.email}",
                extra={
                    "event_type": "user_management",
                    "action": "create_user_failed",
                    "email": user_in.email,
                    "reason": "email_already_exists",
                },
            )

            audit.log_security_event(
                "duplicate_user_registration",
                f"Attempt to register existing email: {user_in.email}",
                severity="low",
                details={"email": user_in.email},
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists.",
            )

        # 2. Validate inputs
        if not user_in.email or not user_in.email.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required.",
            )
        if not user_in.full_name or not user_in.full_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Full name is required.",
            )
        if not user_in.password or not user_in.password.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is required.",
            )

        # 3. Hash the password
        try:
            hashed_password = hash_password(user_in.password)
        except Exception as e:
            logger.error(
                f"Password hashing failed for user: {user_in.email}",
                extra={
                    "event_type": "user_management",
                    "action": "password_hash_failed",
                    "email": user_in.email,
                    "error": str(e),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to hash password.",
            )

        # 4. Create the User
        user_in.email = user_in.email.strip()
        user_in.full_name = user_in.full_name.strip()
        user_in.password = hashed_password

        try:
            created_user = await crud_user.create(db=db, obj_in=user_in)

            # Log successful user creation
            logger.info(
                f"User created successfully: {created_user.email}",
                extra={
                    "event_type": "user_management",
                    "action": "user_created",
                    "user_id": str(created_user.id),
                    "email": created_user.email,
                },
            )

            # Audit log for user creation
            audit.log_user_action(
                user_id=str(created_user.id),
                action="user_registration",
                details={
                    "email": created_user.email,
                    "full_name": created_user.full_name,
                    "is_active": created_user.is_active,
                },
            )

            audit.log_security_event(
                "user_registration",
                f"New user registered: {created_user.email}",
                severity="info",
                details={"user_id": str(created_user.id), "email": created_user.email},
            )

            return created_user

        except Exception as e:
            logger.error(
                f"User creation failed: {user_in.email}",
                extra={
                    "event_type": "user_management",
                    "action": "user_creation_failed",
                    "email": user_in.email,
                    "error": str(e),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user.",
            )

    @log_performance("user_service.update_user")
    async def update_user(
        self, db: AsyncSession, *, user_id: str, user_in: UserUpdate, current_user: User
    ) -> User:
        """Update user with audit logging"""

        logger.info(
            f"Updating user: {user_id}",
            extra={
                "event_type": "user_management",
                "action": "update_user",
                "user_id": user_id,
                "updated_by": str(current_user.id),
            },
        )

        # Get existing user
        user = await crud_user.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update user
        updated_user = await crud_user.update(db, db_obj=user, obj_in=user_in)

        # Log successful update
        audit.log_user_action(
            user_id=str(current_user.id),
            action="user_update",
            resource=f"user:{user_id}",
            details={
                "updated_user_id": user_id,
                "updated_fields": user_in.dict(exclude_unset=True),
            },
        )

        return updated_user

    @log_performance("user_service.get_user_profile")
    async def get_user_profile(
        self, db: AsyncSession, *, user_id: str, requesting_user: User
    ) -> User:
        """Get user profile with data access logging"""

        user = await crud_user.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Log data access for audit
        audit.log_data_access(
            user_id=str(requesting_user.id),
            resource_type="user_profile",
            resource_id=user_id,
            operation="read",
        )

        return user


user_service = UserService()
