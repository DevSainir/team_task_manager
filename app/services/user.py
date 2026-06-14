import uuid

from fastapi import HTTPException, status

from app.core import security
from app.models.user import User
from app.repos.user import UserRepo
from app.schemas.user import UserUpdateIn


class UserService:
    """Service for user-related business logic."""

    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    async def get_user_by_id(self, user_id: uuid.UUID) -> User:
        """Retrieve user by ID or raise 404 if not found."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    async def update_user(self, user: User, payload: UserUpdateIn) -> User:
        """Update specific fields of a user profile."""
        update_data = payload.model_dump(exclude_unset=True)

        if "password" in update_data:
            hashed_password = security.get_password_hash(update_data.pop("password"))
            user.hashed_password = hashed_password

        for key, value in update_data.items():
            setattr(user, key, value)
        await self.user_repo.session.commit()
        await self.user_repo.update(user)
        await self.user_repo.session.refresh(user)
        return user

    async def delete_user(self, user_id: uuid.UUID) -> None:
        """Remove a user and all related data."""
        await self.get_user_by_id(user_id)
        await self.user_repo.delete(user_id)
        await self.user_repo.session.commit()
