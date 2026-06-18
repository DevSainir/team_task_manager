from fastapi import APIRouter, UploadFile, status

from app.api.dependencies import CurrentUser, UserSvc
from app.schemas.user import UserOut, UserUpdateIn

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_my_profile(current_user: CurrentUser, user_service: UserSvc):
    """Get the profile of the currently authenticated user."""
    return await user_service.get_user_by_id(current_user.id)


@router.patch("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_my_profile(
    payload: UserUpdateIn,
    current_user: CurrentUser,
    user_service: UserSvc,
):
    """Update profile information for the authenticated user."""
    return await user_service.update_user(current_user, payload)


@router.post("/me/avatar", response_model=UserOut, status_code=status.HTTP_200_OK)
async def upload_avatar(file: UploadFile, current_user: CurrentUser, user_service: UserSvc):
    """Upload user avatar to S3 and update profile."""
    return await user_service.upload_avatar(current_user.id, file)


@router.delete("/me/avatar", response_model=UserOut, status_code=status.HTTP_200_OK)
async def delete_avatar(current_user: CurrentUser, user_service: UserSvc):
    """Delete user avatar"""
    return await user_service.delete_avatar(current_user.id)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_profile(
    current_user: CurrentUser,
    user_service: UserSvc,
):
    """Delete the authenticated user's account entirely."""
    await user_service.delete_user(current_user.id)
