import uuid

from fastapi import HTTPException, status

from app.models.enums import PriorityEnum
from app.models.task import Task
from app.repos.column import ColumnRepo
from app.repos.task import TaskRepo
from app.repos.user import UserRepo
from app.schemas.task import TaskCreateIn, TaskUpdateIn
from app.services.board import BoardService


class TaskService:
    """Service handling task creation, assignment, and updates."""

    def __init__(
        self,
        user_repo: UserRepo,
        task_repo: TaskRepo,
        column_repo: ColumnRepo,
        board_service: BoardService,
    ):
        self.user_repo = user_repo
        self.task_repo = task_repo
        self.column_repo = column_repo
        self.board_service = board_service

    async def _verify_column_access(self, column_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Helper to verify if a user has access to the board containing the column."""
        column = await self.column_repo.get_by_id(column_id)
        if not column:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
        await self.board_service.get_board(column.board_id, user_id)

    async def create_task(self, payload: TaskCreateIn, user_id: uuid.UUID) -> Task:
        """Create a new task in a specific column."""
        await self._verify_column_access(payload.column_id, user_id)

        if payload.assignee_id:
            assignee = await self.user_repo.get_by_id(payload.assignee_id)
            if not assignee:
                raise HTTPException(status_code=400, detail="Assignee user not found")

        task = Task(
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            position=payload.position,
            deadline=payload.deadline,
            tags=payload.tags,
            column_id=payload.column_id,
            assignee_id=payload.assignee_id,
        )
        created_task = await self.task_repo.create(task)
        await self.task_repo.session.commit()
        await self.task_repo.session.refresh(created_task)
        return created_task

    async def get_filtered_tasks(
        self,
        column_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None,
        priority: PriorityEnum | None,
        assignee_id: uuid.UUID | None,
        limit: int,
        offset: int,
    ) -> list[Task]:
        """Retrieve tasks with access check, filters and pagination."""
        await self._verify_column_access(column_id, user_id)
        return await self.task_repo.get_filtered_tasks(
            column_id, title, priority, assignee_id, limit, offset
        )

    async def update_task(
        self, task_id: uuid.UUID, payload: TaskUpdateIn, user_id: uuid.UUID
    ) -> Task:
        """Update a task (move to another column, change assignee, edit text)."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        await self._verify_column_access(task.column_id, user_id)
        if payload.column_id and payload.column_id != task.column_id:
            await self._verify_column_access(payload.column_id, user_id)

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)

        await self.task_repo.session.commit()
        await self.task_repo.session.refresh(task)
        return task

    async def delete_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a task from the system."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        await self._verify_column_access(task.column_id, user_id)
        await self.task_repo.delete(task_id)
        await self.task_repo.session.commit()
