import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.column import Column


class ColumnRepo:
    """Repository for handling Column database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, column: Column) -> Column:
        """Insert a new column into the database."""
        self.session.add(column)
        await self.session.flush()
        return column

    async def get_by_id(self, column_id: uuid.UUID) -> Column | None:
        """Fetch a column by its UUID."""
        stmt = select(Column).where(Column.id == column_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_board(self, board_id: uuid.UUID) -> list[Column]:
        """Fetch all columns for a specific board ordered by position."""
        stmt = select(Column).where(Column.board_id == board_id).order_by(Column.position)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, column_id: uuid.UUID) -> None:
        """Delete a column from the database."""
        stmt = delete(Column).where(Column.id == column_id)
        await self.session.execute(stmt)
