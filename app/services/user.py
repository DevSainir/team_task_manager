import uuid

from fastapi import HTTPException, UploadFile, status

from app.core import security
from app.infrastructure.storage.s3 import S3Client
from app.models.user import User
from app.repos.user import UserRepo
from app.schemas.user import UserOut, UserUpdateIn


class UserService:
    """Service for user-related business logic."""

    def __init__(self, user_repo: UserRepo, s3_client: S3Client):
        self.user_repo = user_repo
        self.s3_client = s3_client

    def _enrich_user(self, user: User) -> UserOut:
        """Helper to enrich user element with presigned S3 url."""
        user_out = UserOut.model_validate(user)

        if user_out.avatar_url:
            user_out.avatar_url = self.s3_client.generate_presigned_url(user_out.avatar_url)

        return user_out

    async def get_user_by_id(self, user_id: uuid.UUID) -> UserOut:
        """Retrieve user by ID or raise 404 if not found."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return self._enrich_user(user)

    async def update_user(self, user: User, payload: UserUpdateIn) -> UserOut:
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
        return self._enrich_user(user)

    async def upload_avatar(self, user_id: uuid.UUID, file: UploadFile) -> UserOut:
        """Upload an avatar to S3 and save key in database."""
        user = await self.user_repo.get_by_id(user_id)

        if user.avatar_url:
            await self.s3_client.delete_file(user.avatar_url)

        file_key = await self.s3_client.upload_file(file, "avatars", str(user.id))

        user.avatar_url = file_key
        await self.user_repo.session.commit()

        return self._enrich_user(user)

    async def delete_avatar(self, user_id: uuid.UUID) -> UserOut:
        """Remove an avatar from S3 and clear file key in database"""
        user = await self.user_repo.get_by_id(user_id)
        if user.avatar_url:
            await self.s3_client.delete_file(user.avatar_url)
            user.avatar_url = None
            await self.user_repo.session.commit()

        return self._enrich_user(user)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        """Remove a user and all related data."""
        await self.get_user_by_id(user_id)
        user = await self.user_repo.get_by_id(user_id)
        await self.s3_client.delete_file(user.avatar_url)
        await self.user_repo.delete(user_id)
        await self.user_repo.session.commit()
