import uuid

from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUser, TaskSvc
from app.models.enums import PriorityEnum
from app.schemas.task import TaskCreateIn, TaskOut, TaskUpdateIn

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreateIn, current_user: CurrentUser, task_service: TaskSvc):
    """Create a new task in a column."""
    return await task_service.create_task(payload, current_user.id)


@router.get("/column/{column_id}", response_model=list[TaskOut], status_code=status.HTTP_200_OK)
async def get_tasks(
    column_id: uuid.UUID,
    current_user: CurrentUser,
    task_service: TaskSvc,
    title: str | None = Query(None, description="Filter by title"),
    priority: PriorityEnum | None = Query(None, description="Filter by priority"),
    assignee_id: uuid.UUID | None = Query(None, description="Filter by assignee"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get tasks with filtering, sorting, and pagination[cite: 11]."""
    return await task_service.get_filtered_tasks(
        column_id, current_user.id, title, priority, assignee_id, limit, offset
    )


@router.patch("/{task_id}", response_model=TaskOut, status_code=status.HTTP_200_OK)
async def update_task(
    task_id: uuid.UUID, payload: TaskUpdateIn, current_user: CurrentUser, task_service: TaskSvc
):
    """Update task details, assignment, or move to another column."""
    return await task_service.update_task(task_id, payload, current_user.id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: uuid.UUID, current_user: CurrentUser, task_service: TaskSvc):
    """Delete a task."""
    await task_service.delete_task(task_id, current_user.id)
