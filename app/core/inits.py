from contextlib import asynccontextmanager

import pytz
import redis
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi_csrf_jinja.middleware import FastAPICSRFJinjaMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.apis import accounts as apis_accounts
from app.apis.articles import articles as apis_articles
from app.apis.articles import comments as apis_articles_comments
from app.apis import auth as apis_auth
from app.apis import wysiwyg as apis_wysiwyg
from app.core.database import ASYNC_ENGINE
from app.core.redis import redis_client
from app.core.settings import STATIC_DIR, MEDIA_DIR, CONFIG, templates
from app.utils import exc_handler
from app.utils.apschedulers import scheduler, scheduled_lotto_update
from app.utils.commons import to_kst, num_format, urlencode_filter
from app.utils.middleware import AccessTokenSetCookieMiddleware
from app.views import index
from app.views import accounts as views_accounts
from app.views import articles as views_articles
from app.lottos import views as views_lotto

# 한국 시간대 명시적 지정
KST = pytz.timezone('Asia/Seoul')

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing database......")
    # FastAPI 인스턴스 기동시 필요한 작업 수행.
    scheduler.add_job(
        scheduled_lotto_update,
        CronTrigger(day_of_week='sat', hour=23, minute=59, timezone=KST),  # 매주 토요일 오후 11시 59분
        id='lotto_update_job',
        replace_existing=True
    )
    scheduler.start()
    print("Starting Scheduler......")

    try:
        await redis_client.ping() # Redis 연결 테스트
        print("Redis connection established......")
    except redis.exceptions.ConnectionError:
        print("Failed to connect to Redis......")
    print("Starting up...")
    yield
    # FastAPI 인스턴스 종료시 필요한 작업 수행
    await redis_client.aclose()
    print("Redis connection closed......")
    print("Shutting down...")
    await ASYNC_ENGINE.dispose()
    scheduler.shutdown()


def including_middleware(app):
    app.add_middleware(CORSMiddleware,
                       allow_origins=[
                           "http://localhost:5173",  # 프론트엔드 origin (예시)
                           "http://127.0.0.1:5500",  # 필요시 추가
                           "http://localhost:8000",  # 백엔드가 템플릿 제공하는 경우
                       ], # 실제 프론트 주소
                       allow_methods=["*"],
                       allow_headers=["*"],
                       allow_credentials=True,
                       max_age=-1)
    app.add_middleware(FastAPICSRFJinjaMiddleware,
                       secret=CONFIG.SECRET_KEY,
                       cookie_name="csrf_token",
                       header_name="X-CSRF-Token",)
                       # swagger를 CSRF_TOKEN적용에서 제외시키는 방법: 라이브러리에서 제공하는 예외 옵션 이름에 맞춰 사용하세요.
                       # (예: exclude_paths, exempt_paths, exempt_urls 등)
                       # 이 프로젝트는 swagger로 커스터마이징해서 csrf_token을 적용시켰다.
                       # exempt_urls=["/swagger/custom/docs", "/swagger/custom/redoc", "/swagger/custom/openapi.json"])
    """ AccessTokenSetCookieMiddleware: access_token이 만료되면, 
    get_current_user 리프레시로 폴백하면서 액세스토큰을 만들때 가로채서 쿠키에 심는다."""
    app.add_middleware(AccessTokenSetCookieMiddleware)

def including_exception_handler(app):
    app.add_exception_handler(StarletteHTTPException,
                              exc_handler.custom_http_exception_handler)

def including_router(app):
    app.include_router(index.router, prefix="", tags=["IndexViews"])
    app.include_router(apis_accounts.router, prefix="/apis/accounts", tags=["AccountsAPI"])
    app.include_router(apis_auth.router, prefix="/apis/auth", tags=["AuthAPI"])
    # from app.apis.articles import articles as apis_articles # articles 폴더로 refactoring
    app.include_router(apis_articles.router, prefix="/apis/articles", tags=["ArticlesAPI"])
    app.include_router(apis_articles_comments.router, prefix="/apis/articles/comments", tags=["ArticlesCommentsAPI"])
    app.include_router(apis_wysiwyg.router, prefix="/apis/wysiwyg", tags=["WysiwygAPI"])
    app.include_router(views_accounts.router, prefix="/views/accounts", tags=["AccountsViews"])
    app.include_router(views_articles.router, prefix="/views/articles", tags=["ArticlesViews"])

    app.include_router(views_lotto.router, prefix="/lotto", tags=["Lotto"])


def initialize_app():
    app = FastAPI(title=CONFIG.APP_NAME,
                  version=CONFIG.APP_VERSION,
                  description=CONFIG.APP_DESCRIPTION,
                  lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url="/swagger/custom/openapi.json",
                  )
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

    templates.env.globals["STATIC_URL"] = "/static"
    templates.env.globals["MEDIA_URL"] = "/media"
    templates.env.filters["to_kst"] = to_kst
    templates.env.filters["num_format"] = num_format
    templates.env.filters["urlencode"] = urlencode_filter

    including_middleware(app)
    including_exception_handler(app)
    including_router(app)

    return app