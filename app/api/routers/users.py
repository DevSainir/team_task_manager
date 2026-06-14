from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_user_service
from app.models.user import User
from app.schemas.user import UserOut, UserUpdateIn
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get the profile of the currently authenticated user."""
    return current_user


@router.patch("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_my_profile(
    payload: UserUpdateIn,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update profile information for the authenticated user."""
    return await user_service.update_user(current_user, payload)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Delete the authenticated user's account entirely."""
    await user_service.delete_user(current_user.id)
