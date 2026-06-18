import uuid

from fastapi import HTTPException, status

from app.models.column import Column
from app.repos.column import ColumnRepo
from app.schemas.column import ColumnCreateIn, ColumnUpdateIn
from app.services.board import BoardService


class ColumnService:
    """Service handling column operations within boards."""

    def __init__(self, column_repo: ColumnRepo, board_service: BoardService):
        self.column_repo = column_repo
        self.board_service = board_service

    async def create_column(self, payload: ColumnCreateIn, user_id: uuid.UUID) -> Column:
        """Create a column after verifying board access."""
        await self.board_service.get_board(payload.board_id, user_id)
        existing_columns = await self.column_repo.get_all_by_board(payload.board_id)

        for col in existing_columns:
            if col.position >= payload.position:
                col.position += 1

        column = Column(title=payload.title, position=payload.position, board_id=payload.board_id)
        created_column = await self.column_repo.create(column)
        await self.column_repo.session.commit()
        await self.column_repo.session.refresh(created_column)
        return created_column

    async def get_columns_by_board(self, board_id: uuid.UUID, user_id: uuid.UUID) -> list[Column]:
        """Get all columns for a board, verifying access first."""
        await self.board_service.get_board(board_id, user_id)
        return await self.column_repo.get_all_by_board(board_id)

    async def update_column(
        self, column_id: uuid.UUID, payload: ColumnUpdateIn, user_id: uuid.UUID
    ) -> Column:
        """Update column title or position."""
        column = await self.column_repo.get_by_id(column_id)
        if not column:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")

        await self.board_service.get_board(column.board_id, user_id)

        if payload.title:
            column.title = payload.title

        if payload.position is not None and payload.position != column.position:
            old_pos = column.position
            new_pos = payload.position
            existing_columns = await self.column_repo.get_all_by_board(column.board_id)

            for col in existing_columns:
                if col.id == column.id:
                    continue
                if old_pos < new_pos and old_pos < col.position <= new_pos:
                    col.position -= 1
                elif new_pos < old_pos and new_pos <= col.position < old_pos:
                    col.position += 1
            column.position = new_pos

        await self.column_repo.session.commit()
        await self.column_repo.session.refresh(column)
        return column

    async def delete_column(self, column_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete column and all its underlying tasks."""
        column = await self.column_repo.get_by_id(column_id)
        if not column:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")

        await self.board_service.get_board(column.board_id, user_id)
        await self.column_repo.delete(column_id)

        existing_columns = await self.column_repo.get_all_by_board(column.board_id)
        for col in existing_columns:
            if col.position > column.position:
                col.position -= 1

        await self.column_repo.session.commit()
