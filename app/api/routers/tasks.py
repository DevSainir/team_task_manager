import uuid

from fastapi import APIRouter, Body, Query, UploadFile, status

from app.api.dependencies import CurrentUser, TaskSvc
from app.models.enums import PriorityEnum
from app.schemas.task import TaskCreateIn, TaskOut, TaskUpdateIn

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Task successfully created."},
        400: {"description": "Assignee is not found or not a member of this board."},
        403: {"description": "Access denied."},
    },
)
async def create_task(payload: TaskCreateIn, current_user: CurrentUser, task_service: TaskSvc):
    """Create a new task in a column."""
    return await task_service.create_task(payload, current_user.id)


@router.get(
    "/column/{column_id}",
    response_model=list[TaskOut],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Filtered and sorted list of tasks successfully retrieved."},
        403: {"description": "Access denied to the target column or board."},
        401: {"description": "User is not authenticated."},
    },
)
async def get_tasks(
    column_id: uuid.UUID,
    current_user: CurrentUser,
    task_service: TaskSvc,
    title: str | None = Query(None, description="Filter by title"),
    priority: PriorityEnum | None = Query(None, description="Filter by priority"),
    assignee_id: uuid.UUID | None = Query(None, description="Filter by assignee"),
    tags: list[str] | None = Query(None, description="Filter by tags"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get tasks with filtering, sorting, and pagination."""
    return await task_service.get_filtered_tasks(
        column_id, current_user.id, title, priority, assignee_id, tags, limit, offset
    )


@router.patch(
    "/{task_id}",
    response_model=TaskOut,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Task information updated."},
        404: {"description": "Task is not found."},
    },
)
async def update_task(
    task_id: uuid.UUID, payload: TaskUpdateIn, current_user: CurrentUser, task_service: TaskSvc
):
    """Update task details, assignment, or move to another column."""
    return await task_service.update_task(task_id, payload, current_user.id)


@router.post(
    "/{task_id}/attachments",
    response_model=TaskOut,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "File successfully uploaded to s3 and attached to task."},
        403: {"description": "Access denied to this task."},
        404: {"description": "Task or attachment URL not found."},
        503: {"description": "S3 object storage is currently unavailable."},
    },
)
async def upload_task_attachment(
    task_id: uuid.UUID, file: UploadFile, current_user: CurrentUser, task_service: TaskSvc
):
    """Upload files to S3 and attach them to the task"""
    return await task_service.upload_attachment(task_id, current_user.id, file)


@router.delete(
    "/{task_id}/attachments",
    response_model=TaskOut,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Attachment successfully deleted from the task and S3 storage."},
        403: {"description": "Access denied to this task."},
        404: {"description": "Task or attachment URL not found."},
    },
)
async def delete_task_attachment(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    task_service: TaskSvc,
    url: str = Body(..., embed=True),
):
    """Remove attachments from S3 and key from database"""
    return await task_service.delete_attachment(task_id, current_user.id, url)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Task successfully deleted."},
        403: {"description": "Access denied. Not enough permissions to delete this task."},
        404: {"description": "Task not found."},
    },
)
async def delete_task(task_id: uuid.UUID, current_user: CurrentUser, task_service: TaskSvc):
    """Delete a task."""
    await task_service.delete_task(task_id, current_user.id)
