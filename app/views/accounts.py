from fastapi import APIRouter, Request, Depends

from app.core.settings import templates
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.schemas.accounts import UserOut
from app.services.account_service import UserService, get_user_service
from app.utils.accounts import validate_self_user
from app.utils.commons import get_times, render_with_times

router = APIRouter()


@router.get("/register")
async def register(request: Request):
    return await render_with_times(request, "accounts/register.html")


@router.get("/login")
async def login(request: Request):
    return await render_with_times(request, "accounts/login.html")


@router.get("/account/{user_id}", response_model=UserOut,
            summary="특정 회원 조회 HTML", description="회원의 ID 기반으로 특정 회원 조회 templates.TemplateResponse",
            responses={404: {
                "description": "회원 조회 실패",
                "content": {"application/json": {"example": {"detail": "회원을 찾을 수 없습니다."}}}
            }})
async def get_user_by_id(request: Request, user_id: int,
                         user_service: UserService = Depends(get_user_service),
                         current_user: User = Depends(get_current_user)):
    user = await validate_self_user(user_id, current_user, user_service)
    extra = {
        "current_user": user,
    }
    return await render_with_times(request, "accounts/detail.html", extra)


@router.get("/lost/password/reset")
async def lost_password_reset(request: Request):
    return await render_with_times(request, "accounts/lost.html")


@router.get("/username/update/{user_id}")
async def username_update(request: Request, user_id: int,
                          user_service: UserService = Depends(get_user_service),
                          current_user: User = Depends(get_current_user)):
    user = await validate_self_user(user_id, current_user, user_service)
    extra = {
        "current_user": user,
        "username": current_user.username,
    }
    return await render_with_times(request, "accounts/each.html", extra)


@router.get("/email/update/{user_id}")
async def email_update(request: Request, user_id: int,
                       user_service: UserService = Depends(get_user_service),
                       current_user: User = Depends(get_current_user)):
    user = await validate_self_user(user_id, current_user, user_service)
    extra = {
        "current_user": user,
        "email": current_user.email,
    }
    return await render_with_times(request, "accounts/each.html", extra)


@router.get("/password/update/{user_id}")
async def password_update(request: Request, user_id: int,
                          user_service: UserService = Depends(get_user_service),
                          current_user: User = Depends(get_current_user)):
    user = await validate_self_user(user_id, current_user, user_service)
    extra = {
        "current_user": user,
        "password": "password",
    }
    return await render_with_times(request, "accounts/each.html", extra)


@router.get("/profile/image/update/{user_id}")
async def profile_image_update(request: Request, user_id: int,
                               user_service: UserService = Depends(get_user_service),
                               current_user: User = Depends(get_current_user)):
    user = await validate_self_user(user_id, current_user, user_service)
    extra = {
        "current_user": user,
        "image": "image",
    }
    return await render_with_times(request, "accounts/each.html", extra)
