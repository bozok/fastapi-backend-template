from pydantic import EmailStr
from sqlmodel import SQLModel, Field
from typing import Optional
import uuid
from datetime import datetime


class UserBase(SQLModel):
    email: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)


class UserCreate(SQLModel):
    email: EmailStr
    full_name: str
    password: str


class UserRead(SQLModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None


class UserUpdate(SQLModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    last_login: Optional[datetime] = None
