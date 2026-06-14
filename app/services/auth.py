import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from app.core import security
from app.core.config import settings
from app.models.auth import RefreshSession
from app.models.user import User
from app.repos.auth import AuthRepo
from app.repos.user import UserRepo
from app.schemas.auth import UserLoginIn
from app.schemas.user import UserCreateIn


class AuthService:
    """Service for authentication and session management."""

    def __init__(self, user_repo: UserRepo, auth_repo: AuthRepo):
        self.user_repo = user_repo
        self.auth_repo = auth_repo
        self.dummy_hash = security.get_password_hash("secret")

    async def register_user(self, payload: UserCreateIn) -> User:
        """Register a new user and prevent duplicate emails."""
        existing_user = await self.user_repo.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists"
            )

        new_user = User(
            email=payload.email,
            hashed_password=security.get_password_hash(payload.password),
            full_name=payload.full_name,
        )
        await self.user_repo.create(new_user)
        await self.user_repo.session.commit()
        await self.user_repo.session.refresh(new_user)
        return new_user

    async def authenticate_user(self, payload: UserLoginIn) -> User:
        """Validate credentials and protect against timing attacks."""
        user = await self.user_repo.get_by_email(payload.email)

        if not user:
            security.verify_password(payload.password, self.dummy_hash)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not security.verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

        return user

    async def create_tokens(self, user: User) -> tuple[str, str]:
        """Generate access/refresh tokens and register DB session."""
        access_token = security.create_access_token(user.id)

        jti = str(uuid.uuid4())
        refresh_token = security.create_refresh_token(user.id, jti)

        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session = RefreshSession(
            user_id=user.id,
            refresh_token_jti=jti,
            expires_at=expires_at,
        )
        await self.auth_repo.create_session(session)
        await self.auth_repo.session.commit()

        return access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        """Process refresh token, validate rotation, and issue new pair."""
        try:
            payload = security.decode_token(refresh_token)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            ) from e

        jti = payload.get("jti")
        user_id = uuid.UUID(payload.get("sub"))

        session = await self.auth_repo.get_session_by_jti(jti)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found"
            )

        if session.is_used or session.expires_at < datetime.now(UTC):
            await self.auth_repo.delete_all_user_sessions(user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token compromised or expired. Sessions terminated.",
            )

        await self.auth_repo.mark_session_used(session.id)

        user = await self.user_repo.get_by_id(user_id)
        return await self.create_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        """Invalidate the specific session in the database."""
        try:
            payload = security.decode_token(refresh_token)
            jti = payload.get("jti")
            session = await self.auth_repo.get_session_by_jti(jti)
            if session:
                await self.auth_repo.delete_session(session.id)
                await self.auth_repo.session.commit()
        except Exception:
            pass
