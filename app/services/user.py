# app/services/user_service.py

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
import uuid

from app.crud.user import user as crud_user
from app.models.user import User
from app.schemas.user import UserCreate


class UserService:
    async def create(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        """
        Handles the business logic for creating a user, including validation,
        password hashing.
        """
        # 1. Validate Email Existence
        existing_user = await crud_user.get_by_email(db, email=user_in.email)
        if existing_user:
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

        # 3. Create the User
        user_in.email = user_in.email.strip()
        user_in.full_name = user_in.full_name.strip()

        created_user = await crud_user.create(db=db, obj_in=user_in)

        return created_user

    async def get_by_id(self, db: AsyncSession, *, user_id: uuid.UUID) -> User:
        user = await crud_user.get(db, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    # async def get_users(self, db: AsyncSession, *, pagination_params: PaginationParams) -> List[User]:


user_service = UserService()
