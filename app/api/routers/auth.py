from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app.api.dependencies import get_auth_service
from app.schemas.auth import TokenOut, UserLoginIn
from app.schemas.user import UserCreateIn, UserOut
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreateIn, auth_service: AuthService = Depends(get_auth_service)):
    """Register a new user account."""
    return await auth_service.register_user(payload)


@router.post("/login", response_model=TokenOut, status_code=status.HTTP_200_OK)
async def login(
    payload: UserLoginIn, response: Response, auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user, set httpOnly cookie, and return access token."""
    user = await auth_service.authenticate_user(payload)

    access_token, refresh_token = await auth_service.create_tokens(user)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800,
    )
    return TokenOut(access_token=access_token)


@router.post("/refresh", response_model=TokenOut, status_code=status.HTTP_200_OK)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh the access token and rotate the refresh token."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing"
        )

    new_access, new_refresh = await auth_service.refresh_tokens(refresh_token)

    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=604800,
    )
    return TokenOut(access_token=new_access)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Invalidate session in DB and clear cookie."""
    if refresh_token:
        await auth_service.logout(refresh_token)
    response.delete_cookie(key="refresh_token")
