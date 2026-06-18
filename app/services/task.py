import uuid

from fastapi import HTTPException, UploadFile, status

from app.infrastructure.storage.s3 import S3Client
from app.models.enums import PriorityEnum
from app.models.task import Task
from app.repos.column import ColumnRepo
from app.repos.task import TaskRepo
from app.repos.user import UserRepo
from app.schemas.task import TaskCreateIn, TaskOut, TaskUpdateIn
from app.services.board import BoardService


class TaskService:
    """Service handling task creation, assignment, and updates."""

    def __init__(
        self,
        user_repo: UserRepo,
        task_repo: TaskRepo,
        column_repo: ColumnRepo,
        board_service: BoardService,
        s3_client: S3Client,
    ):
        self.user_repo = user_repo
        self.task_repo = task_repo
        self.column_repo = column_repo
        self.board_service = board_service
        self.s3_client = s3_client

    async def _verify_column_access(self, column_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Helper to verify if a user has access to the board containing the column."""
        column = await self.column_repo.get_by_id(column_id)
        if not column:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
        await self.board_service.get_board(column.board_id, user_id)

    async def _verify_assignee(
        self, assignee_id: uuid.UUID, column_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> None:
        """Check if assignee is a member of the board."""
        column = await self.column_repo.get_by_id(column_id)
        board = await self.board_service.get_board(column.board_id, current_user_id)

        valid_user_ids = [member.id for member in board.members]
        if assignee_id not in valid_user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of this board",
            )

    def _enrich_task(self, task: Task) -> TaskOut:
        """Helper to enrich task with attachments presigned S3 urls."""
        task_out = TaskOut.model_validate(task)
        if task_out.attachment_urls:
            task_out.attachment_urls = [
                self.s3_client.generate_presigned_url(key) for key in task_out.attachment_urls
            ]
        return task_out

    async def get_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> Task:
        """Retrieve a task and verify access."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        await self._verify_column_access(task.column_id, user_id)
        return task

    async def create_task(self, payload: TaskCreateIn, user_id: uuid.UUID) -> TaskOut:
        """Create a new task in a specific column."""
        await self._verify_column_access(payload.column_id, user_id)

        if payload.assignee_id:
            await self._verify_assignee(payload.assignee_id, payload.column_id, user_id)

        existing_tasks = await self.task_repo.get_filtered_tasks(payload.column_id)
        for t in existing_tasks:
            if t.position >= payload.position:
                t.position += 1

        task = Task(**payload.model_dump())
        created_task = await self.task_repo.create(task)
        await self.task_repo.session.commit()
        await self.task_repo.session.refresh(created_task)
        return self._enrich_task(created_task)

    async def get_filtered_tasks(
        self,
        column_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str | None,
        priority: PriorityEnum | None,
        assignee_id: uuid.UUID | None,
        tags: list[str] | None,
        limit: int,
        offset: int,
    ) -> list[Task]:
        """Retrieve tasks with access check, filters and pagination."""
        await self._verify_column_access(column_id, user_id)
        return await self.task_repo.get_filtered_tasks(
            column_id, title, priority, assignee_id, tags, limit, offset
        )

    async def update_task(
        self, task_id: uuid.UUID, payload: TaskUpdateIn, user_id: uuid.UUID
    ) -> TaskOut:
        """Update a task (move to another column, change assignee, edit text)."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        await self._verify_column_access(task.column_id, user_id)

        old_col = task.column_id
        new_col = payload.column_id if payload.column_id is not None else old_col
        old_pos = task.position
        new_pos = payload.position if payload.position is not None else old_pos

        if old_col != new_col:
            await self._verify_column_access(new_col, user_id)

        if payload.assignee_id and payload.assignee_id != task.assignee_id:
            await self._verify_assignee(payload.assignee_id, new_col, user_id)

        if old_col != new_col:
            old_tasks = await self.task_repo.get_filtered_tasks(old_col)
            for t in old_tasks:
                if t.position > old_pos:
                    t.position -= 1
            new_tasks = await self.task_repo.get_filtered_tasks(new_col)
            for t in new_tasks:
                if t.position >= new_pos:
                    t.position += 1
        else:
            if new_pos != old_pos:
                tasks = await self.task_repo.get_filtered_tasks(old_col)
                for t in tasks:
                    if t.id == task.id:
                        continue
                    if old_pos < new_pos and old_pos < t.position <= new_pos:
                        t.position -= 1
                    elif new_pos < old_pos and new_pos <= t.position < old_pos:
                        t.position += 1

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)

        await self.task_repo.session.commit()
        await self.task_repo.session.refresh(task)
        return self._enrich_task(task)

    async def upload_attachment(
        self, task_id: uuid.UUID, user_id: uuid.UUID, file: UploadFile
    ) -> TaskOut:
        """Upload files to S3 and save key to database"""
        task = await self.get_task(task_id, user_id)

        file_key = await self.s3_client.upload_file(file, "tasks", str(task_id))

        current_keys = list(task.attachment_urls)
        current_keys.append(file_key)
        task.attachment_urls = current_keys

        await self.task_repo.session.commit()
        await self.task_repo.session.refresh(task)

        return self._enrich_task(task)

    async def delete_attachment(
        self, task_id: uuid.UUID, user_id: uuid.UUID, url_to_delete: str
    ) -> TaskOut:
        """Remove attachments from S3 and clear file key in database"""
        task = await self.get_task(task_id, user_id)

        target_key = None
        for key in task.attachment_urls:
            if key in url_to_delete:
                target_key = key
                break

        if not target_key:
            raise HTTPException(status_code=404, detail="Attachment not found in this task")

        await self.s3_client.delete_file(target_key)

        current_keys = list(task.attachment_urls)
        current_keys.remove(target_key)
        task.attachment_urls = current_keys

        await self.task_repo.session.commit()
        await self.task_repo.session.refresh(task)

        return self._enrich_task(task)

    async def delete_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a task from the system."""
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        await self._verify_column_access(task.column_id, user_id)
        await self.task_repo.delete(task_id)
        await self.task_repo.session.commit()
