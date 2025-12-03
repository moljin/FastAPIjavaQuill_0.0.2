from typing import Literal, TypedDict
from fastapi import Request

from app.core.settings import CONFIG


class CookieAttrs(TypedDict):
    secure: bool
    samesite: Literal["lax", "strict", "none"]

def _is_https(request: Request) -> bool:
    forwarded = request.headers.get("x-forwarded-proto")
    scheme = (forwarded or request.url.scheme or "").lower()
    return scheme == "https"

def compute_cookie_attrs(request: Request, *, cross_site: bool = False) -> CookieAttrs:
    """
    cross_site=True: 다른 사이트로 전송이 필요한 쿠키(예: 제3자 컨텍스트)일 때만 사용.
    개발 환경에서는 SameSite=None을 강제로 금지하고 Lax로 대체합니다.
    """
    is_https = _is_https(request)
    app_env = (CONFIG.APP_ENV or "").lower()

    # 기본값: same-site 시나리오
    if not cross_site:
        return CookieAttrs(secure=False if app_env == "development" else is_https, samesite="lax")

    # cross-site 시나리오
    if app_env == "development":
        # 개발에서는 None 금지 -> 경고 회피 및 로컬 디버깅 편의성
        return CookieAttrs(secure=False, samesite="lax")

    # 프로덕션: HTTPS일 때만 None + Secure
    if is_https:
        return CookieAttrs(secure=True, samesite="none")

    # 프로덕션이지만 http 인식인 경우(프록시 미설정 등): 안전하게 Lax로 폴백
    return CookieAttrs(secure=False, samesite="lax")