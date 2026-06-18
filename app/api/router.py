from fastapi import APIRouter

from app.api.routers import auth, boards, columns, tasks, users

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(boards.router)
api_router.include_router(columns.router)
api_router.include_router(tasks.router)
