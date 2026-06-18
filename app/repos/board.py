import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.board import Board
from app.models.column import Column


class BoardRepo:
    """Repository for handling Board database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, board: Board) -> Board:
        """Insert a new board into the database."""
        self.session.add(board)
        await self.session.flush()
        return board

    async def get_by_id(self, board_id: uuid.UUID) -> Board | None:
        """Fetch a board by its UUID, including members."""
        stmt = select(Board).where(Board.id == board_id).options(selectinload(Board.members))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_detailed_by_id(self, board_id: uuid.UUID) -> Board | None:
        """Fetch a board with full hierarchy: members, columns, and tasks."""
        stmt = (
            select(Board)
            .where(Board.id == board_id)
            .options(
                selectinload(Board.members), selectinload(Board.columns).selectinload(Column.tasks)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_user(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Board]:
        """Fetch all boards where user is owner or member."""
        stmt = (
            select(Board)
            .where((Board.owner_id == user_id) | (Board.members.any(id=user_id)))
            .options(selectinload(Board.members))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.unique().scalars().all())

    async def delete(self, board_id: uuid.UUID) -> None:
        """Delete a board from the database."""
        stmt = delete(Board).where(Board.id == board_id)
        await self.session.execute(stmt)
