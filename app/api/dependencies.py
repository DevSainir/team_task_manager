from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import security
from app.core.config import settings
from app.infrastructure.storage.s3 import S3Client, get_s3_client
from app.models.user import User
from app.repos.auth import AuthRepo
from app.repos.board import BoardRepo
from app.repos.column import ColumnRepo
from app.repos.task import TaskRepo
from app.repos.user import UserRepo
from app.services.auth import AuthService
from app.services.board import BoardService
from app.services.column import ColumnService
from app.services.task import TaskService
from app.services.user import UserService

engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

http_bearer = HTTPBearer()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider for AsyncSession."""
    async with async_session_maker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
S3Dep = Annotated[S3Client, Depends(get_s3_client)]


def get_user_repo(session: SessionDep) -> UserRepo:
    """Dependency provider for UserRepo."""
    return UserRepo(session)


def get_auth_repo(session: SessionDep) -> AuthRepo:
    """Dependency provider for AuthRepo."""
    return AuthRepo(session)


def get_board_repo(session: SessionDep) -> BoardRepo:
    """Dependency provider for BoardRepo."""
    return BoardRepo(session)


def get_column_repo(session: SessionDep) -> ColumnRepo:
    """Dependency provider for ColumnRepo."""
    return ColumnRepo(session)


def get_task_repo(session: SessionDep) -> TaskRepo:
    """Dependency provider for TaskRepo."""
    return TaskRepo(session)


def get_auth_service(
    user_repo: Annotated[UserRepo, Depends(get_user_repo)],
    auth_repo: Annotated[AuthRepo, Depends(get_auth_repo)],
) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(user_repo=user_repo, auth_repo=auth_repo)


def get_user_service(
    user_repo: Annotated[UserRepo, Depends(get_user_repo)], s3_client: S3Dep
) -> UserService:
    """Dependency provider for UserService."""
    return UserService(user_repo=user_repo, s3_client=s3_client)


def get_board_service(
    board_repo: Annotated[BoardRepo, Depends(get_board_repo)],
    column_repo: Annotated[ColumnRepo, Depends(get_column_repo)],
    task_repo: Annotated[TaskRepo, Depends(get_task_repo)],
    user_repo: Annotated[UserRepo, Depends(get_user_repo)],
    s3_client: S3Dep,
) -> BoardService:
    """Dependency provider for BoardService."""
    return BoardService(
        board_repo=board_repo,
        column_repo=column_repo,
        task_repo=task_repo,
        user_repo=user_repo,
        s3_client=s3_client,
    )


def get_column_service(
    column_repo: Annotated[ColumnRepo, Depends(get_column_repo)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
) -> ColumnService:
    """Dependency provider for ColumnService."""
    return ColumnService(column_repo=column_repo, board_service=board_service)


def get_task_service(
    user_repo: Annotated[UserRepo, Depends(get_user_repo)],
    task_repo: Annotated[TaskRepo, Depends(get_task_repo)],
    column_repo: Annotated[ColumnRepo, Depends(get_column_repo)],
    board_service: Annotated[BoardService, Depends(get_board_service)],
    s3_client: S3Dep,
) -> TaskService:
    """Dependency provider for TaskService."""
    return TaskService(
        user_repo=user_repo,
        task_repo=task_repo,
        column_repo=column_repo,
        board_service=board_service,
        s3_client=s3_client,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    user_repo: UserRepo = Depends(get_user_repo),
) -> User:
    """Dependency provider for receiving current user and checking access."""
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


CurrentUser = Annotated["User", Depends(get_current_user)]
AuthSvc = Annotated[AuthService, Depends(get_auth_service)]
UserSvc = Annotated[UserService, Depends(get_user_service)]
BoardSvc = Annotated[BoardService, Depends(get_board_service)]
ColumnSvc = Annotated[ColumnService, Depends(get_column_service)]
TaskSvc = Annotated[TaskService, Depends(get_task_service)]
