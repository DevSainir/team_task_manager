import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.models.enums import PriorityEnum


def empty_to_none(v: str | uuid.UUID | None) -> uuid.UUID | None:
    if v == "":
        return None
    return v


AssigneeId = Annotated[uuid.UUID | None, BeforeValidator(empty_to_none)]
TitleStr = Annotated[str, Field(min_length=1, max_length=255)]
PositionInt = Annotated[int, Field(ge=0)]


class TaskBase(BaseModel):
    """Base schema for Task attributes."""

    title: TitleStr
    description: str | None = None
    priority: PriorityEnum = PriorityEnum.medium
    position: PositionInt
    deadline: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class TaskCreateIn(TaskBase):
    """Schema for creating a new Task."""

    column_id: uuid.UUID
    assignee_id: AssigneeId = None


class TaskUpdateIn(BaseModel):
    """Schema for updating an existing Task."""

    title: TitleStr | None = None
    description: str | None = None
    priority: PriorityEnum | None = None
    position: PositionInt | None = None
    deadline: datetime | None = None
    tags: list[str] | None = None
    column_id: uuid.UUID | None = None
    assignee_id: AssigneeId = None


class TaskOut(TaskBase):
    """Schema for Task response."""

    model_config = ConfigDict(from_attributes=True)

    attachment_urls: list[str] = Field(default_factory=list)
    id: uuid.UUID
    column_id: uuid.UUID
    assignee_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
