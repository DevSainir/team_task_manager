import uuid

from fastapi import APIRouter, status

from app.api.dependencies import ColumnSvc, CurrentUser
from app.schemas.column import ColumnCreateIn, ColumnOut, ColumnUpdateIn

router = APIRouter(prefix="/columns", tags=["Columns"])


@router.post("", response_model=ColumnOut, status_code=status.HTTP_201_CREATED)
async def create_column(
    payload: ColumnCreateIn, current_user: CurrentUser, column_service: ColumnSvc
):
    """Create a new column in a board."""
    return await column_service.create_column(payload, current_user.id)


@router.get("/board/{board_id}", response_model=list[ColumnOut], status_code=status.HTTP_200_OK)
async def get_columns_by_board(
    board_id: uuid.UUID, current_user: CurrentUser, column_service: ColumnSvc
):
    """Get all columns for a specific board."""
    return await column_service.get_columns_by_board(board_id, current_user.id)


@router.patch("/{column_id}", response_model=ColumnOut, status_code=status.HTTP_200_OK)
async def update_column(
    column_id: uuid.UUID,
    payload: ColumnUpdateIn,
    current_user: CurrentUser,
    column_service: ColumnSvc,
):
    """Update column position or title."""
    return await column_service.update_column(column_id, payload, current_user.id)


@router.delete("/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(column_id: uuid.UUID, current_user: CurrentUser, column_service: ColumnSvc):
    """Delete a column and its tasks."""
    await column_service.delete_column(column_id, current_user.id)
