import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.task import TaskOut

TitleStr = Annotated[str, Field(min_length=1, max_length=255)]
PositionInt = Annotated[int, Field(ge=0)]


class ColumnBase(BaseModel):
    """Base schema for Column attributes."""

    title: TitleStr
    position: PositionInt


class ColumnCreateIn(ColumnBase):
    """Schema for creating a new Column."""

    board_id: uuid.UUID


class ColumnUpdateIn(BaseModel):
    """Schema for updating an existing Column."""

    title: TitleStr | None = None
    position: PositionInt | None = None


class ColumnOut(ColumnBase):
    """Schema for Column response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    board_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ColumnWithTasksOut(ColumnOut):
    """Deep schema for column that includes its tasks."""

    tasks: list[TaskOut] = []
