from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, UserSvc
from app.schemas.user import UserOut, UserUpdateIn

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_my_profile(current_user: CurrentUser):
    """Get the profile of the currently authenticated user."""
    return current_user


@router.patch("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_my_profile(
    payload: UserUpdateIn,
    current_user: CurrentUser,
    user_service: UserSvc,
):
    """Update profile information for the authenticated user."""
    return await user_service.update_user(current_user, payload)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_profile(
    current_user: CurrentUser,
    user_service: UserSvc,
):
    """Delete the authenticated user's account entirely."""
    await user_service.delete_user(current_user.id)
