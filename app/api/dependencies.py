from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import security
from app.core.config import settings
from app.models.user import User
from app.repos.auth import AuthRepo
from app.repos.user import UserRepo
from app.services.auth import AuthService
from app.services.user import UserService

engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

http_bearer = HTTPBearer()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> UserRepo:
    return UserRepo(session)


def get_auth_repo(session: AsyncSession = Depends(get_db_session)) -> AuthRepo:
    return AuthRepo(session)


def get_auth_service(
    user_repo: UserRepo = Depends(get_user_repo),
    auth_repo: AuthRepo = Depends(get_auth_repo),
) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(user_repo=user_repo, auth_repo=auth_repo)


def get_user_service(user_repo: UserRepo = Depends(get_user_repo)) -> UserService:
    """Dependency provider for UserService."""
    return UserService(user_repo=user_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    user_repo: UserRepo = Depends(get_user_repo),
) -> User:
    token = credentials.credentials
    try:
        payload = security.decode_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    import uuid

    user = await user_repo.get_by_id(uuid.UUID(user_id_str))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user
