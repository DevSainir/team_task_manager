import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.column import ColumnWithTasksOut
from app.schemas.user import UserWithRoleOut

TitleStr = Annotated[str, Field(min_length=1, max_length=255)]


class BoardBase(BaseModel):
    """Base schema for Board attributes."""

    title: TitleStr


class BoardCreateIn(BoardBase):
    """Schema for creating a new Board."""

    pass


class BoardUpdateIn(BaseModel):
    """Schema for updating an existing Board."""

    title: TitleStr | None = None


class BoardOut(BoardBase):
    """Schema for Board response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class BoardDetailOut(BoardOut):
    """Deep schema for a single board, including columns, tasks, and members."""

    columns: list[ColumnWithTasksOut] = []
    members: list[UserWithRoleOut] = []


class BoardListOut(BoardOut):
    """Schema for returning board list with user role."""

    role: str = "member"
