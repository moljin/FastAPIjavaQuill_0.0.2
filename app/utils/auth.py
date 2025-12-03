import asyncio
from datetime import datetime, timedelta, timezone
import time
from typing import Optional, Any

from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, HTTPException

from app.core.database import get_db
from app.core.settings import CONFIG
from app.models.users import User
from app.utils.commons import refresh_expire

"""
JWT 액세스 토큰을 생성합니다.
"""

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    # 만료 시간 설정(30분)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta # 넘어온 값: timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=CONFIG.ACCESS_TOKEN_EXPIRE)

    # JWT 페이로드에 만료 시간 추가
    to_encode.update({
        "exp": expire,
    })

    # JWT 토큰 생성 (스레드로 오프로드)
    encoded_jwt = await asyncio.to_thread(jwt.encode,
                                          to_encode,
                                          CONFIG.SECRET_KEY,
                                          algorithm=CONFIG.ALGORITHM)
    print("create_access_token ", encoded_jwt)
    return encoded_jwt


"""
JWT refresh 토큰을 생성합니다.
"""

async def create_refresh_token(data: dict) -> str:
    user_id = data["user_id"]
    # 만료 시간 설정(7일)
    _REFRESH_COOKIE_EXPIRE = refresh_expire()
    expire = _REFRESH_COOKIE_EXPIRE

    # JWT 페이로드에 만료 시간과 고유 ID 추가
    refresh_payload = {
        "user_id": user_id,
        "exp": expire,
        "type": "refresh"  # 토큰 타입 명시
    }

    # JWT 토큰 생성 (스레드로 오프로드)
    encoded_jwt = await asyncio.to_thread(jwt.encode,
                                          refresh_payload,
                                          CONFIG.SECRET_KEY,
                                          algorithm=CONFIG.ALGORITHM)
    print("create_refresh_token ", encoded_jwt)
    return encoded_jwt


"""
JWT 토큰을 검증하고 페이로드를 반환합니다.
"""

# AI Chat 권장: 동기 함수로 두는 것이 좋습니다.
def verify_token(token: str, *, type_: Optional[str] = None) -> Optional[dict[str, Any]]:
    # 디버깅용 로그 (원한다면 유지)
    try:
        unverified = jwt.get_unverified_claims(token)
        exp_ts = unverified.get("exp")
        if exp_ts:
            print("============== 해당 token의 만료기간 관련 정보 ==============")
            print("exp:", datetime.fromtimestamp(exp_ts, tz=timezone.utc))
            print("now:", datetime.now(timezone.utc))
            print("seconds_left:", int(exp_ts - datetime.now(timezone.utc).timestamp()))
    except Exception as e:
        print("get_unverified_claims 실패는 단순 디버깅 용도이므로 그대로 진행", e)
        pass

    try:
        payload = jwt.decode(token, CONFIG.SECRET_KEY, algorithms=[CONFIG.ALGORITHM])
        print("verify_token payload == :::::", payload)
        if type_ is not None and payload.get("type") != type_:
            # 타입 불일치 시 무효
            return None
        return payload
    except ExpiredSignatureError:
        print("verify_token: token expired")
        return None
    except JWTError as e:
        print("verify_token: jwt error:", repr(e))
        return None

async def payload_to_user(access_token: str, db: AsyncSession = Depends(get_db) ):
    payload = verify_token(access_token)
    print("payload_to_user: payload:::: ", payload)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="존재하지 않는 사용자입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 토큰에서 사용자명 추출
    # username = payload.get("username") # username 변경시 변경된 username때문데 User를 찾을 수 없다.
    # if username is None:
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="인증되지 않은 사용자입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 사용자 조회
    # query = (select(User).where(User.username == username)) # username 변경시 변경된 username때문데 User를 찾을 수 없다.
    query = (select(User).where(User.id == user_id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print("payload_to_user: user:::: : ", user)
    return user
"""
JWT 토큰의 남은 만료 시간을 초 단위로 계산
"""

# AI chat: 요약: 대부분의 경우 동기 함수로 두는 것이 더 낫습니다.
def get_token_expiry(token: str) -> int:
    try:
        payload = jwt.decode(token, CONFIG.SECRET_KEY, algorithms=[CONFIG.ALGORITHM])
        # payload = await asyncio.to_thread(
        #     jwt.decode,
        #     token,
        #     SECRET_KEY,
        #     algorithms=[ALGORITHM]
        # )

        exp = payload.get("exp")

        if exp is not None:
            # exp가 숫자 타임스탬프이거나 datetime일 수 있음
            if isinstance(exp, (int, float)):
                remaining = exp - time.time()
            elif isinstance(exp, datetime):
                remaining = (exp - datetime.now()).total_seconds()
            else:
                remaining = 0

            # 최소 1초 이상 설정
            return max(int(remaining), 1)

    except:
        pass

    # 기본값 (30분)
    return CONFIG.ACCESS_TOKEN_EXPIRE * 60
