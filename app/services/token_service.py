from datetime import timedelta
from typing import Optional

from app.core.redis import get_redis_client
from app.core.settings import CONFIG

TOKEN_BLACKLIST_PREFIX = "blacklist:"  # 토큰 블랙리스트 키 접두사
REFRESH_TOKEN_PREFIX = "refresh:"  # Refresh 토큰 저장 접두사
DEFAULT_TOKEN_EXPIRY = 60 * 30  # 토큰 유효 기간 (초)


class AsyncTokenService:
    """
    Redis asyncio 클라이언트를 사용하는 비동기 토큰 서비스
    """

    @classmethod
    async def blacklist_token(cls, token: str, expires_in: int = DEFAULT_TOKEN_EXPIRY) -> bool:
        redis_client = get_redis_client()
        key = f"{TOKEN_BLACKLIST_PREFIX}{token}"

        try:
            await redis_client.set(key, "1", ex=expires_in)
        except Exception as e:
            print(f"Redis 연결 오류 발생, 재시도 중: {e}")
            # 연결 초기화
            await redis_client.close()

            # 전역 변수 초기화를 위해 redis.py의 로직을 다시 타게 함
            import app.core.redis as redis_module
            redis_module.redis_client = None
            new_client = get_redis_client()

            # 재시도
            await new_client.set(key, "1", ex=expires_in)

        return True

    @classmethod
    async def is_token_blacklisted(cls, token: str) -> bool:
        redis_client = get_redis_client()
        key = f"{TOKEN_BLACKLIST_PREFIX}{token}"

        try:
            return bool(await redis_client.exists(key))
        except Exception as e:
            print(f"Redis 연결 오류 발생, 재시도 중: {e}")
            await redis_client.close()

            import app.core.redis as redis_module
            redis_module.redis_client = None
            new_client = get_redis_client()

            return bool(await new_client.exists(key))

    @classmethod
    async def clear_blacklist(cls) -> None:
        redis_client = get_redis_client()

        async def execute_clear(client):
            keys = []
            async for key in client.scan_iter(match=f"{TOKEN_BLACKLIST_PREFIX}*"):
                keys.append(key)
            if keys:
                await client.delete(*keys)

        try:
            await execute_clear(redis_client)
        except Exception as e:
            print(f"Redis 연결 오류 발생, 재시도 중: {e}")
            await redis_client.close()

            import app.core.redis as redis_module
            redis_module.redis_client = None
            new_client = get_redis_client()

            await execute_clear(new_client)

    @classmethod
    async def store_refresh_token(cls, user_id: int, refresh_token: str) -> bool:
        redis_client = get_redis_client()
        user_key = f"{REFRESH_TOKEN_PREFIX}{user_id}"
        print("store_refresh_token user_key: ")

        expire_seconds = int(timedelta(days=CONFIG.REFRESH_TOKEN_EXPIRE + 1).total_seconds())
        print("store_refresh_token expire_seconds: ", expire_seconds)

        # asyncio 파이프라인
        # 로그인 시 Refresh Token을 Redis에 저장하는 순간 터졌습니다.
        # pipeline 사용 시 반드시 예외 처리 + 재시도
        async def execute_storage(client):
            async with client.pipeline(transaction=True) as pipe:
                await pipe.sadd(user_key, refresh_token)
                await pipe.expire(user_key, expire_seconds)
                await pipe.execute()

        try:
            await execute_storage(redis_client)
        except Exception as e:
            print(f"Redis 연결 오류 발생, 재시도 중: {e}")
            # 연결 초기화 (redis.py 구조에 따라 client를 새로 고침)
            await redis_client.close()

            # 전역 변수 초기화를 위해 redis.py의 로직을 다시 타게 함
            import app.core.redis as redis_module
            redis_module.redis_client = None
            new_client = get_redis_client()

            # 재시도 (한 번 더 실패하면 상위로 예외 던짐)
            await execute_storage(new_client)

        return True

    @classmethod
    async def validate_refresh_token(cls, user_id: int, refresh_token: str) -> bool:
        redis_client = get_redis_client()
        user_key = f"{REFRESH_TOKEN_PREFIX}{user_id}"

        try:
            return bool(await redis_client.sismember(user_key, refresh_token))
        except Exception as e:
            print(f"Redis 연결 오류 발생, 재시도 중: {e}")
            await redis_client.close()

            import app.core.redis as redis_module
            redis_module.redis_client = None
            new_client = get_redis_client()

            return bool(await new_client.sismember(user_key, refresh_token))

    @classmethod
    async def revoke_refresh_token(cls, user_id: int, refresh_token: Optional[str] = None) -> bool:
        redis_client = get_redis_client()
        user_key = f"{REFRESH_TOKEN_PREFIX}{user_id}"

        async def execute_revoke(client):
            if refresh_token:
                await client.srem(user_key, refresh_token)
            else:
                await client.delete(user_key)

        try:
            await execute_revoke(redis_client)
        except Exception as e:
            print(f"Redis 연결 오류 발생, 재시도 중: {e}")
            await redis_client.close()

            import app.core.redis as redis_module
            redis_module.redis_client = None
            new_client = get_redis_client()

            await execute_revoke(new_client)

        return True
