import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base schema for User attributes."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    is_active: bool = True


class UserCreateIn(UserBase):
    """Schema for creating a new User."""

    password: str = Field(min_length=8, max_length=128)


class UserUpdateIn(BaseModel):
    """Schema for updating an existing User."""

    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    avatar_url: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserOut(UserBase):
    """Schema for User response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime
