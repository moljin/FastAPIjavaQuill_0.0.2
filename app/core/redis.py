from redis.asyncio import Redis, ConnectionPool

from app.core.settings import CONFIG

# # Connection Pool 기반 access ##############################
""" # AI Chat # 비동기적으로 ConnectionPool 적용
비동기 Redis 클라이언트와 함께 쓰려면 동기용 ConnectionPool이 아니라 asyncio 전용 풀을 써야 합니다.
즉, redis.ConnectionPool이 아니라 redis.asyncio.ConnectionPool을 사용해야 합니다.
from redis.asyncio import Redis, ConnectionPool
예시 1) asyncio용 ConnectionPool을 직접 생성해서 사용
"""

'''마땅히 설정할 곳이 없어서... 서버 구동시작시 여기를 지나가므로 전역변수처럼 사용'''
ACCESS_COOKIE_MAX_AGE = CONFIG.ACCESS_TOKEN_EXPIRE * 60 # 초 1800 : 30분
CODE_TTL_SECONDS = 10 * 60  # 10분


host = CONFIG.REDIS_HOST if CONFIG.APP_ENV == "production" else "localhost"
port = CONFIG.REDIS_PORT if CONFIG.APP_ENV == "production" else 6379
password = CONFIG.REDIS_PASSWORD if CONFIG.APP_ENV == "production" else None
db = CONFIG.REDIS_DB if CONFIG.APP_ENV == "production" else 0


# 각 worker 프로세스마다 독립적인 연결을 생성하기 위해 None으로 초기화
redis_pool = None
redis_client = None

def get_redis_pool():
    """각 worker 프로세스마다 독립적인 connection pool 생성

    gunicorn의 여러 worker 프로세스 간 Redis 연결 공유 문제 해결:
    - asyncio 기반 Redis 클라이언트는 프로세스 간 공유 불가
    - 각 worker가 자체 연결 풀을 생성하도록 lazy initialization 적용
    """
    global redis_pool
    if redis_pool is None:
        redis_pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            max_connections=10,
            socket_keepalive=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
    return redis_pool

def get_redis_client():
    """각 worker 프로세스마다 독립적인 Redis client 생성

    사용법:
        redis_client = get_redis_client()
        await redis_client.set("key", "value")
    """
    global redis_client
    if redis_client is None:
        redis_client = Redis(connection_pool=get_redis_pool())
    return redis_client
