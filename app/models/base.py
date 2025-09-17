from datetime import datetime, timezone
import uuid
from sqlmodel import Field, SQLModel
import sqlalchemy as sa
from sqlalchemy.orm import declared_attr


class TableNameModel:
    """Mixin to automatically generate table names from class names"""

    @declared_attr
    def __tablename__(cls) -> str:
        # Convert CamelCase to snake_case for table names
        import re

        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


class RawModel(SQLModel):
    """RawModel model with common fields for all database models"""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        description="Unique identifier for the record",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=sa.Column(
            sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        description="Timestamp when the record was created",
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=sa.Column(
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        description="Timestamp when the record was last updated",
    )


class BaseModel(RawModel, TableNameModel):
    """
    The base for all table models. It includes UUIDs, timestamps,
    and automatic table name generation. The key is that this class
    does NOT set `table=True`. The final model that inherits from it will.
    """

    pass
