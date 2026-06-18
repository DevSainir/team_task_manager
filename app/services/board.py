import uuid

from fastapi import HTTPException, status

from app.infrastructure.storage.s3 import S3Client
from app.models.board import Board
from app.models.column import Column
from app.repos.board import BoardRepo
from app.repos.column import ColumnRepo
from app.repos.task import TaskRepo
from app.repos.user import UserRepo
from app.schemas.board import BoardCreateIn, BoardDetailOut, BoardListOut, BoardUpdateIn


class BoardService:
    """Service handling board business logic and access control."""

    DEFAULT_COLUMNS = ["To Do", "In Progress", "Done"]

    def __init__(
        self,
        board_repo: BoardRepo,
        column_repo: ColumnRepo,
        task_repo: TaskRepo,
        user_repo: UserRepo,
        s3_client: S3Client,
    ):
        self.board_repo = board_repo
        self.column_repo = column_repo
        self.task_repo = task_repo
        self.user_repo = user_repo
        self.s3_client = s3_client

    @staticmethod
    def _check_user_access(board: Board, user_id: uuid.UUID) -> None:
        """Private helper to verify if user is owner or member."""
        is_owner = board.owner_id == user_id
        is_member = any(member.id == user_id for member in board.members)
        if not (is_owner or is_member):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this board"
            )

    @staticmethod
    def _enrich_board_list(board: Board, user_id: uuid.UUID) -> BoardListOut:
        """Helper to enrich board list element"""
        board_out = BoardListOut.model_validate(board)
        board_out.role = "owner" if board.owner_id == user_id else "member"
        return board_out

    def _enrich_detailed_board(self, board: Board) -> BoardDetailOut:
        """Helper to enrich board element with members, columns, tasks and presigned S3 urls"""
        board_out = BoardDetailOut.model_validate(board)

        for member in board_out.members:
            member.role = "owner" if member.id == board.owner_id else "member"
            if member.avatar_url:
                member.avatar_url = self.s3_client.generate_presigned_url(member.avatar_url)

        for col in board_out.columns:
            for task in col.tasks:
                if task.attachment_urls:
                    task.attachment_urls = [
                        self.s3_client.generate_presigned_url(k) for k in task.attachment_urls
                    ]

        return board_out

    async def create_board(self, payload: BoardCreateIn, owner_id: uuid.UUID) -> Board:
        """Create a new board and automatically generate default columns."""
        board = Board(title=payload.title, owner_id=owner_id)
        owner = await self.user_repo.get_by_id(owner_id)
        board.members.append(owner)

        created_board = await self.board_repo.create(board)

        for idx, col_title in enumerate(self.DEFAULT_COLUMNS):
            await self.column_repo.create(
                Column(title=col_title, position=idx, board_id=created_board.id)
            )

        await self.board_repo.session.commit()
        await self.board_repo.session.refresh(created_board)
        return created_board

    async def get_user_boards(
        self, user_id: uuid.UUID, limit: int, offset: int
    ) -> list[BoardListOut]:
        """Retrieve all boards available to the user (owned and joined)."""
        boards = await self.board_repo.get_all_by_user(user_id, limit, offset)
        return [self._enrich_board_list(board, user_id) for board in boards]

    async def get_board(self, board_id: uuid.UUID, user_id: uuid.UUID) -> Board:
        """Retrieve a board and verify access."""
        board = await self.board_repo.get_by_id(board_id)
        if not board:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")

        self._check_user_access(board, user_id)
        return board

    async def get_detailed_board(self, board_id: uuid.UUID, user_id: uuid.UUID) -> BoardDetailOut:
        """Retrieve a fully populated board and verify access."""
        board = await self.board_repo.get_detailed_by_id(board_id)
        if not board:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")

        self._check_user_access(board, user_id)
        return self._enrich_detailed_board(board)

    async def invite_member(
        self, board_id: uuid.UUID, email: str, current_user_id: uuid.UUID
    ) -> Board:
        """Add a new user to the board members list."""
        board = await self.get_board(board_id, current_user_id)
        if board.owner_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can invite"
            )

        user_to_invite = await self.user_repo.get_by_email(email)
        if not user_to_invite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user_to_invite.id == board.owner_id or user_to_invite in board.members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User already in board"
            )

        board.members.append(user_to_invite)
        await self.board_repo.session.commit()
        await self.board_repo.session.refresh(board)
        return board

    async def remove_member(
        self, board_id: uuid.UUID, user_id_to_remove: uuid.UUID, current_user_id: uuid.UUID
    ) -> None:
        """Remove a member from the board or allow a member to leave."""
        board = await self.get_board(board_id, current_user_id)

        if board.owner_id != current_user_id and current_user_id != user_id_to_remove:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to remove this user",
            )

        if board.owner_id == user_id_to_remove:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Owner cannot leave the board. Delete the board instead.",
            )

        user_to_remove = await self.user_repo.get_by_id(user_id_to_remove)
        if not user_to_remove:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User to remove not found in the system",
            )

        if user_to_remove not in board.members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User is not a member of this board"
            )

        board.members.remove(user_to_remove)
        await self.task_repo.clear_tasks_assignee(board_id, user_id_to_remove)
        await self.board_repo.session.commit()

    async def update_board(
        self, board_id: uuid.UUID, payload: BoardUpdateIn, current_user_id: uuid.UUID
    ) -> Board:
        """Update board details (Owner only)."""
        board = await self.get_board(board_id, current_user_id)

        if board.owner_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the board owner can update its details",
            )

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(board, key, value)

        await self.board_repo.session.commit()
        await self.board_repo.session.refresh(board)
        return board

    async def delete_board(self, board_id: uuid.UUID, current_user_id: uuid.UUID) -> None:
        """Delete a board (owner only)."""
        board = await self.get_board(board_id, current_user_id)
        if board.owner_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can delete"
            )
        await self.board_repo.delete(board_id)
        await self.board_repo.session.commit()
