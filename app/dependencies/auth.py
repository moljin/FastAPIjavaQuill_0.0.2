from typing import Optional, Set

from fastapi import Depends, HTTPException, Request, status, Response, Security

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose.exceptions import ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import ACCESS_COOKIE_MAX_AGE
from app.core.settings import CONFIG
from app.models.users import User
from app.services.auth_service import AuthService
from app.utils.auth import payload_to_user
from app.utils.cookies import compute_cookie_attrs

# 헤더는 선택적으로만 받도록 설정 (없어도 에러 발생 X)
bearer_scheme = HTTPBearer(auto_error=False)

"""
토큰에서 현재 사용자 정보를 가져오는 의존성 함수
"""

async def get_current_user(
        request: Request, response: Response,
        credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
        db: AsyncSession = Depends(get_db),
):
    # 1) 헤더
    auth = request.headers.get("authorization")
    print("1. get_current_user 시작  ::: auth::::::: ", auth)
    access_token = auth.split(" ", 1)[1].strip() if auth and auth.lower().startswith("bearer ") else None
    print("2. get_current_user 시작 ::: access_token::::::: ", access_token)

    # 2) 쿠키 폴백
    if not access_token:
        access_token = request.cookies.get(CONFIG.ACCESS_COOKIE_NAME)
    print("3. get_current_user 시작 ::: request.cookies.get access_token::::::: ", access_token)
    if access_token:
        try:
            user = await payload_to_user(access_token, db)
            print("get_current_user 끝 if access_token: user::::::: ", user)
            return user
        except ExpiredSignatureError:
            pass  # 3) 리프레시 시도

    # 3) 리프레시 폴백 (공통 함수 호출)
    refresh_token = request.cookies.get(CONFIG.REFRESH_COOKIE_NAME)
    print("4. refresh_access_token_from_cookie: refresh_token: ", refresh_token)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    auth_service = AuthService(db=db)
    token_payload = await auth_service.refresh_access_token(refresh_token)
    if not token_payload:
        # refresh 토큰이 유효하지 않거나 만료된 경우
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token is invalid or expired",
        )

    new_access = token_payload.get(CONFIG.ACCESS_COOKIE_NAME)
    if not new_access:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to issue access token")

    # request.state에 보관 (뷰에서 꺼내서 실제 TemplateResponse에 심을 수 있게)
    request.state.new_access = new_access
    attrs = compute_cookie_attrs(request, cross_site=False)
    print("1. attrs['secure']: ", attrs["secure"])
    print("2. attrs['samesite']: ", attrs["samesite"])
    response.set_cookie(
        key=CONFIG.ACCESS_COOKIE_NAME,
        value=new_access,
        httponly=True,
        secure=attrs["secure"],  # HTTPS라면 True
        samesite=attrs["samesite"],
        path="/",
        max_age=ACCESS_COOKIE_MAX_AGE,
    )

    user = await payload_to_user(new_access, db)

    print("get_current_user 끝 refresh_access_token) 리프레시 폴백: user::::::: ", user)
    return user


async def get_optional_current_user(request: Request, response: Response,
                                    db: AsyncSession = Depends(get_db)) -> Optional[User]:
    """
    인증 토큰이 없거나 유효하지 않은 경우 None을 반환하고, 다른 예외는 그대로 전달합니다.
    AI Chat:
        - 익명 접근을 허용하는 엔드포인트에서는 Depends(get_optional_current_user)를 사용하세요.
            이것을 적용하고 if current_user is None or current_user != user 로 분기하여 "Not authorized: 접근권한이 없습니다."로 raise 날려도 된다.
            그러면, Depends(get_current_user) 주입해서, "Not authenticated: 로그인하지 않았습니다."를 raise 날리는 것과 효과가 같다.
            효과는 같지만, 엄밀한 의미에서는 다르다.
        - 인증이 반드시 필요한 엔드포인트는 기존처럼 Depends(get_current_user)를 유지하면 됩니다.
    """
    try:
        # 핵심: get_current_user를 직접 호출하되, db를 명시적으로 전달
        return await get_current_user(request=request, response=response, db=db)
    except HTTPException as e:
        if e.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            return None
        raise


# def allow_usernames(*allowed_names: str):
def allow_usernames(allowed_names: list):
    """ AI Chat이 알려준 방식임
    특정 username만 접근을 허용하는 FastAPI 의존성 팩토리.
    ADMINS = ["admin", "owner"]
    사용 예) Depends(allow_usernames(ADMINS))
    """
    allowed: Set[str] = {n.strip() for n in allowed_names if n and n.strip()}
    if not allowed:
        raise ValueError("allow_usernames requires at least one non-empty username")

    async def dependency(user = Depends(get_current_user)):
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        username = getattr(user, "username", None)
        if not username or username not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You Don't Have Permission to Access This Resource.",
            )
        return user  # 필요 시 엔드포인트에서 user를 그대로 사용 가능

    return dependency
