import os
from functools import lru_cache
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv

from fastapi.templating import Jinja2Templates
from fastapi_csrf_jinja.jinja_processor import csrf_token_processor
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

""" # SECRET_KEY 생성하는 방법
# (.venv) PS D:\Python_FastAPI\My_Advanced\FastAPIjavaQuill_0.0.1> python
# Python 3.13.5 (tags/v3.13.5:6cb20a2, Jun 11 2025, 16:15:46) [MSC v.1943 64 bit (AMD64)] on win32
# Type "help", "copyright", "credits" or "license" for more information.
>>> import secrets
>>> secrets.token_hex(35)
"""

try:
    '''
    설정 모듈 최상단에서 반드시 .env를 먼저 로드한 뒤에 os.getenv를 호출하세요.
    '''
    load_dotenv(".env", override=False, encoding="utf-8")
except Exception as e:
    print(f"load_dotenv error: {e}")
    '''
    python-dotenv 미설치 등인 경우에도, 설정 로딩은 pydantic-settings가 처리하므로 무시 가능
    '''
    pass

PRESENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = Path(__file__).resolve().parent.parent.parent  ## root폴더
TEMPLATE_DIR = os.path.join(APP_DIR, 'templates')
STATIC_DIR = os.path.join(APP_DIR, 'static')
MEDIA_DIR = os.path.join(APP_DIR, 'media')

ADMINS = [os.getenv("ADMIN_1"), os.getenv("ADMIN_2")]
LOTTO_LATEST_URL = os.getenv("LOTTO_LATEST_URL")
LOTTO_FILEPATH = os.path.join(MEDIA_DIR, os.getenv("LOTTO_FILEPATH"))

templates = Jinja2Templates(
    directory=TEMPLATE_DIR,
    context_processors=[csrf_token_processor("csrf_token", "X-CSRF-Token")]
)

class Settings(BaseSettings):
    """여기에서 값이 비어있는 것은 .env 파일에서 채워진다.
    그 값은 override 되지 않는다. 흐름상 그럴것 같기는 한데...???
    최종적으로 .env에 설정된 값으로 채워져 버리는 것인것 같다."""
    APP_ENV: str = "development"
    APP_NAME: str = "FastAPI_Jinja"
    APP_VERSION: str = "0.0.0"
    APP_DESCRIPTION: str = ("FastAPI_Jinja/Javascript을 이용한 프로젝트 개발: \n"
                            "Jinja Template를 이용하여 Server Side Rendering을 적용하고, \n"
                            "데이터 입력과정을 pydantic schema적용하고 POST 메서드에서 vanilla javascript를 이용하여 개발 진행")

    DEBUG: bool = False

    # 기본값은 두지 않고 .env에서 읽히도록 둡니다.
    SECRET_KEY: Optional[str] = None
    ALGORITHM: str

    DB_TYPE: str
    DB_DRIVER: str

    # 이메일/인증코드
    SMTP_FROM: str  # = os.getenv("SMTP_FROM", SMTP_USERNAME)
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_PORT: int  # = int(os.getenv("SMTP_PORT", 587))
    SMTP_HOST: str  # = os.getenv("SMTP_HOST", "smtp.gmail.com")

    # 액세스/리프페시 토큰
    ACCESS_COOKIE_NAME: str
    REFRESH_COOKIE_NAME: str
    NEW_ACCESS_COOKIE_NAME: str
    NEW_REFRESH_COOKIE_NAME: str

    ACCESS_TOKEN_EXPIRE: int
    REFRESH_TOKEN_EXPIRE: int

    # Media Store Path
    PROFILE_IMAGE_URL: str
    ARTICLE_THUMBNAIL_DIR: str
    ARTICLE_EDITOR_USER_IMG_DIR: str
    ARTICLE_EDITOR_USER_VIDEO_DIR: str
    ARTICLE_COMMENT_EDITOR_USER_IMG_DIR: str
    ARTICLE_COMMENT_EDITOR_USER_VIDEO_DIR: str

    ORIGINS: List[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


class DevSettings(Settings):
    DEBUG: bool = Field(..., validation_alias="DEBUG_TRUE")

    ORIGINS: str = Field(..., validation_alias="DEV_ORIGINS")

    DB_NAME: str = Field(..., validation_alias="DEV_DB_NAME")
    DB_HOST: str = Field(..., validation_alias="DEV_DB_HOST")
    DB_PORT: str = Field(..., validation_alias="DEV_DB_PORT")
    DB_USER: str = Field(..., validation_alias="DEV_DB_USER")
    DB_PASSWORD: str = Field(..., validation_alias="DEV_DB_PASSWORD")


class ProdSettings(Settings):
    APP_NAME: str = Field(..., validation_alias="PROD_APP_NAME")
    APP_VERSION: str = Field(..., validation_alias="PROD_APP_VERSION")
    APP_DESCRIPTION: str = Field(..., validation_alias="PROD_APP_DESCRIPTION")

    ORIGINS: str = Field(..., validation_alias="PROD_ORIGINS")

    DB_NAME: str = Field(..., validation_alias="PROD_DB_NAME")
    DB_HOST: str = Field(..., validation_alias="PROD_DB_HOST")
    DB_PORT: str = Field(..., validation_alias="PROD_DB_PORT")
    DB_USER: str = Field(..., validation_alias="PROD_DB_USER")
    DB_PASSWORD: str = Field(..., validation_alias="PROD_DB_PASSWORD")

    REDIS_HOST: str = Field(..., validation_alias="REDIS_HOST")
    REDIS_PORT: str = Field(..., validation_alias="REDIS_PORT")
    REDIS_DB: str = Field(..., validation_alias="REDIS_DB")
    REDIS_PASSWORD: str = Field(..., validation_alias="REDIS_PASSWORD")

    # 운영에서는 SECRET_KEY 필수
    @model_validator(mode="after")
    def ensure_secret_key(self):
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 16:
            raise ValueError("In production, SECRET_KEY must be set and sufficiently long.")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    print("1. setting start... Only One")
    # model_config의 env_file 설정만으로도 충분하지만, 아래 호출이 있어도 문제는 없습니다.
    app_env = os.getenv("APP_ENV", "development").strip().lower()
    if app_env == "production":
        return ProdSettings()
    print("2. settings...APP_ENV: ", app_env)
    return DevSettings()

CONFIG = get_settings()