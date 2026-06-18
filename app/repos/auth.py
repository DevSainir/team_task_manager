import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import RefreshSession


class AuthRepo:
    """Repository for handling authentication database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, refresh_session: RefreshSession) -> RefreshSession:
        self.session.add(refresh_session)
        await self.session.flush()
        return refresh_session

    async def get_session_by_jti(self, jti: str) -> RefreshSession | None:
        stmt = select(RefreshSession).where(RefreshSession.refresh_token_jti == jti)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_session_used(self, session_id: uuid.UUID) -> None:
        stmt = update(RefreshSession).where(RefreshSession.id == session_id).values(is_used=True)
        await self.session.execute(stmt)

    async def delete_all_user_sessions(self, user_id: uuid.UUID) -> None:
        stmt = delete(RefreshSession).where(RefreshSession.user_id == user_id)
        await self.session.execute(stmt)

    async def delete_session(self, session_id: uuid.UUID) -> None:
        stmt = delete(RefreshSession).where(RefreshSession.id == session_id)
        await self.session.execute(stmt)
