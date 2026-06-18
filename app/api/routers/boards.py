import uuid

from fastapi import APIRouter, Body, Query, status

from app.api.dependencies import BoardSvc, CurrentUser
from app.schemas.board import BoardCreateIn, BoardDetailOut, BoardListOut, BoardOut, BoardUpdateIn

router = APIRouter(prefix="/boards", tags=["Boards"])


@router.post("", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
async def create_board(payload: BoardCreateIn, current_user: CurrentUser, board_service: BoardSvc):
    """Create a new board (automatically generates default columns)."""
    return await board_service.create_board(payload, current_user.id)


@router.get("", response_model=list[BoardListOut], status_code=status.HTTP_200_OK)
async def get_my_boards(
    current_user: CurrentUser,
    board_service: BoardSvc,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get all boards the authenticated user owns or is a member of."""
    return await board_service.get_user_boards(current_user.id, limit, offset)


@router.get("/{board_id}", response_model=BoardDetailOut, status_code=status.HTTP_200_OK)
async def get_board(board_id: uuid.UUID, current_user: CurrentUser, board_service: BoardSvc):
    """Retrieve detailed board info (includes columns, tasks, and members)."""
    return await board_service.get_detailed_board(board_id, current_user.id)


@router.post("/{board_id}/invite", response_model=BoardOut, status_code=status.HTTP_200_OK)
async def invite_member(
    board_id: uuid.UUID,
    current_user: CurrentUser,
    board_service: BoardSvc,
    email: str = Body(..., embed=True),
):
    """Invite an existing user to the board by email (Owner only)."""
    return await board_service.invite_member(board_id, email, current_user.id)


@router.delete("/{board_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    board_id: uuid.UUID, current_user: CurrentUser, board_service: BoardSvc, user_id: uuid.UUID
):
    """Remove an existing user from the board (Owner only). Or leave the board (For user)"""
    return await board_service.remove_member(board_id, user_id, current_user.id)


@router.patch("/{board_id}", response_model=BoardOut, status_code=status.HTTP_200_OK)
async def update_board(
    board_id: uuid.UUID, payload: BoardUpdateIn, current_user: CurrentUser, board_service: BoardSvc
):
    """Update board title (restricted to board owner)."""
    return await board_service.update_board(board_id, payload, current_user.id)


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(board_id: uuid.UUID, current_user: CurrentUser, board_service: BoardSvc):
    """Delete a board and all its content."""
    await board_service.delete_board(board_id, current_user.id)
