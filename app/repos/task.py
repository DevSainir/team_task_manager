import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Column
from app.models.enums import PriorityEnum
from app.models.task import Task


class TaskRepo:
    """Repository for handling Task database operations and filtering."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task: Task) -> Task:
        """Insert a new task into the database."""
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        """Fetch a task by its UUID."""
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_filtered_tasks(
        self,
        column_id: uuid.UUID,
        title: str | None = None,
        priority: PriorityEnum | None = None,
        assignee_id: uuid.UUID | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Task]:
        """Fetch tasks with filtering, sorting and pagination."""
        stmt = select(Task).where(Task.column_id == column_id)

        if title:
            stmt = stmt.where(Task.title.ilike(f"%{title}%"))
        if priority:
            stmt = stmt.where(Task.priority == priority)
        if assignee_id:
            stmt = stmt.where(Task.assignee_id == assignee_id)
        if tags:
            stmt = stmt.where(Task.tags.contains(tags))

        stmt = stmt.order_by(Task.position).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def clear_tasks_assignee(self, board_id: uuid.UUID, member_id: uuid.UUID) -> None:
        stmt = (
            update(Task)
            .where(
                Task.column_id.in_(select(Column.id).where(Column.board_id == board_id)),
                Task.assignee_id == member_id,
            )
            .values(assignee_id=None)
        )
        await self.session.execute(stmt)

    async def delete(self, task_id: uuid.UUID) -> None:
        """Delete a task from the database."""
        stmt = delete(Task).where(Task.id == task_id)
        await self.session.execute(stmt)
