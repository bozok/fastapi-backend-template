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
        hashed_password = hash_password(obj_in.password)
        db_obj = User(**obj_in_data, hashed_password=hashed_password)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


user = CRUDUser(User)
