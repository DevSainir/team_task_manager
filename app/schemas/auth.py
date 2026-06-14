from pydantic import BaseModel, EmailStr, Field


class UserLoginIn(BaseModel):
    """Schema for user login credentials."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenOut(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    token_type: str = "Bearer"
