from typing import Dict, Any, Union
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.crud.base import CRUDBase
from app.core.security import hash_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> User:
        statement = select(User).where(User.email == email)
        result = await db.exec(statement)
        return result.first()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        # obj_in_data = jsonable_encoder(obj_in)
        obj_in_data = obj_in.model_dump(exclude={"password"})

        # Check if password is already hashed (from service layer)
        # Hashed passwords start with algorithm prefix like $2b$
        if obj_in.password.startswith("$"):
            hashed_password = obj_in.password  # Already hashed
        else:
            hashed_password = hash_password(obj_in.password)  # Need to hash

        db_obj = User(**obj_in_data, hashed_password=hashed_password)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: Union[UserUpdate, Dict[str, Any]],
    ) -> User:
        """Update user with password hashing support."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        # Hash password if it's being updated
        if "password" in update_data:
            hashed_password = hash_password(update_data["password"])
            update_data["hashed_password"] = hashed_password
            del update_data["password"]

        # Update fields
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


user = CRUDUser(User)
