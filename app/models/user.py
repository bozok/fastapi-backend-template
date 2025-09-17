# app/models/user.py

from datetime import datetime
from sqlmodel import Field, Column, DateTime
from typing import Optional
from app.models.base import BaseModel


class User(BaseModel, table=True):
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    hashed_password: str = Field(nullable=False)
    is_active: Optional[bool] = Field(default=True)
    last_login: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
