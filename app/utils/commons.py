import datetime
import random
import re
import shutil
import urllib.parse
import uuid
from typing import LiteralString

from email_validator import validate_email, EmailNotValidError
from fastapi import status, UploadFile, HTTPException, Request
import os
import aiofiles as aio
from pydantic_core import PydanticCustomError
from starlette.concurrency import run_in_threadpool

from app.core.settings import MEDIA_DIR, CONFIG, templates
from app.models.users import User


# 로컬파트/도메인 유효성 정규식
EMAIL_LOCAL_RE = re.compile(
    r"^(?![.])(?!.*[.]{2})[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*(?<!\.)$"
)
DOMAIN_LABEL_RE = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$")
TLD_ALPHA_RE = re.compile(r"^[A-Za-z]{2,24}$")
INVALID_EMAIL: LiteralString = "올바른 이메일 형식이 아닙니다."
#
def strict_email(v):
    if v is None:
        print(f"Email Strict Validation Error: ", '빈 값은 허용되지 않습니다.')
        raise PydanticCustomError('empty_value', "올바른 이메일 형식이 아닙니다.")

    s = str(v).strip()
    if not s:
        print(f"Email Strict Validation Error: ", '빈 값은 허용되지 않습니다.')
        raise PydanticCustomError('empty_value', INVALID_EMAIL)

    if s.count('@') != 1:
        print(f"Email Strict Validation Error: ", '올바른 이메일 형식이 아닙니다.')
        raise PydanticCustomError('invalid_email', INVALID_EMAIL)

    local, domain = s.split('@', 1)

    # 길이 제한
    if len(s) > 254:
        print(f"Email Strict Validation Error: ", '이메일 전체 길이가 너무 깁니다(최대 254).')
        raise PydanticCustomError('invalid_email', INVALID_EMAIL)
    if len(local) > 64:
        print(f"Email Strict Validation Error: ", '로컬파트 길이가 너무 깁니다(최대 64).')
        raise PydanticCustomError('invalid_email', INVALID_EMAIL)

    # 로컬파트(dot-atom) 검증
    if not EMAIL_LOCAL_RE.fullmatch(local):
        print(f"Email Strict Validation Error: ", '허용되지 않는 이메일 로컬파트입니다.')
        raise PydanticCustomError('invalid_email', INVALID_EMAIL)

    # 도메인 정규화 및 검증
    domain = domain.lower().rstrip('.')  # 끝의 점(FQDN 표기) 제거
    if not domain:
        print(f"Email Strict Validation Error: ", '올바른 이메일 형식이 아닙니다.')
        raise PydanticCustomError('invalid_email', INVALID_EMAIL)
    if len(domain) > 253:
        print(f"Email Strict Validation Error: ", '도메인 길이가 너무 깁니다(최대 253).')
        raise PydanticCustomError('invalid_email', INVALID_EMAIL)

    labels = domain.split('.')
    if len(labels) < 2:
        print(f"Email Strict Validation Error: ", '도메인에 점(.)이 최소 1개 포함되어야 합니다.')
        raise PydanticCustomError('invalid_email', INVALID_EMAIL)

    for label in labels:
        if not DOMAIN_LABEL_RE.fullmatch(label):
            print(f"Email Strict Validation Error: ", '허용되지 않는 도메인 라벨이 포함되어 있습니다.')
            raise PydanticCustomError('invalid_email', INVALID_EMAIL)

    tld = labels[-1]
    # TLD: 영문 2~24자 또는 punycode(xn--)
    if tld.startswith('xn--'):
        if not (5 <= len(tld) <= 63):
            print(f"Email Strict Validation Error: ", '유효하지 않은 최상위 도메인입니다.')
            raise PydanticCustomError('invalid_email', INVALID_EMAIL)
    else:
        if not TLD_ALPHA_RE.fullmatch(tld):
            print(f"Email Strict Validation Error: ", '유효하지 않은 최상위 도메인입니다.')
            raise PydanticCustomError('invalid_email', INVALID_EMAIL)
    if tld.isdigit():
        print(f"Email Strict Validation Error: ", '유효하지 않은 최상위 도메인입니다.')
        raise PydanticCustomError('invalid_email', INVALID_EMAIL)

    # 정상: 정규화(도메인은 소문자)
    return f"{local}@{domain}"

#
async def random_string(length:int, _type:str):
    if _type == "full":
        string_pool = "0za1qw2sc3de4rf5vb6gt7yh8nm9juiklop"
    elif _type == "string":
        string_pool = "abcdefghijklmnopqrstuvwxyz"
    else:
        string_pool = "0123456789"
    result = random.choices(string_pool, k=length)
    seperator = ""
    return seperator.join(result)
#
async def file_renaming(username:str, ext:str):
    date = datetime.datetime.now().strftime("%Y%m%d_%H%M_%S%f")
    random_str = await random_string(8, "full")
    new_filename = f"{username}_{date}{random_str}"
    return f"{new_filename}{ext}"
#
async def upload_single_image(path:str, user: User, imagefile: UploadFile = None):
    try:
        upload_dir = f"{path}"+"/"+f"{user.id}"+"/" # d/t Linux
        url = await file_write_return_url(upload_dir, user, imagefile, "media", _type="image")
        return url

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="이미지 파일이 제대로 Upload되지 않았습니다. ")

#
async def file_write_return_url(upload_dir: str, user: User, file: UploadFile, _dir: str, _type: str):
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    filename_only, ext = os.path.splitext(file.filename)
    if len(file.filename.strip()) > 0 and len(filename_only) > 0:
        upload_filename = await file_renaming(user.username, ext)
        file_path = upload_dir + upload_filename

        async with aio.open(file_path, "wb") as outfile:
            if _type == "image":
                _CHUNK = 1024 * 1024
                while True:
                    chunk = await file.read(_CHUNK)
                    if not chunk:
                        break
                    await outfile.write(chunk)
            elif _type == "video":
                # await outfile.write(await file.read())
                # 대용량 업로드: 청크 단위로 읽어서 바로 쓰기 (메모리 사용 최소화)
                _CHUNK = 8 * 1024 * 1024  # 8MB
                while True:
                    chunk = await file.read(_CHUNK)
                    if not chunk:
                        break
                    await outfile.write(chunk)
                await outfile.flush()

        url = file_path.split(_dir)[1]
        return url
    else:
        return None

#
"""# 존재 체크-후-삭제 사이에 경쟁 상태가 생길 수 있슴, 
권장: 존재 여부 체크 없이 바로 삭제 시도 (경쟁 상태 방지)"""
async def remove_file_path(path:str): # 파일 삭제
    try:
        await run_in_threadpool(os.remove, path)
    except FileNotFoundError:
        pass  # 이미 없으면 무시

#
async def remove_empty_dir(_dir:str): # 빈 폴더 삭제
    try:
        await run_in_threadpool(os.rmdir, _dir)  # 비어 있을 때만 성공
    except FileNotFoundError:
        pass  # 이미 사라졌다면 무시
    except OSError as e:
        print("비어있지 않거나 잠겨 있는 경우: ", e)
        pass  # 비어있지 않거나 잠겨 있으면 무시(필요 시 로깅)


async def remove_dir_with_files(_dir:str): # 파일을 포함하여 폴더 삭제
    try:
        await run_in_threadpool(shutil.rmtree, _dir)
        # 이미지 저장 디렉토리 및 파일을 삭제, ignore_errors, onerror 파라미터 넣지 않아도 작동한다.
    except FileNotFoundError:
        pass

#
async def old_image_remove(filename:str, path:str):
    try:
        filename_only, ext = os.path.splitext(filename)
        if len(filename.strip()) > 0 and len(filename_only) > 0 and path is not None:
            # old_image_path = f'{APP_DIR}{path}' # \\없어도 된다. url 맨 앞에 \\ 있다.
            old_image_path = f'{MEDIA_DIR}'+'/'+f'{path}'
            await remove_file_path(old_image_path)

    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="이미지 파일이 제대로 Upload되지 않았습니다. ")


# ----------------- 유틸: 이메일 유효성 체크 -----------------
def is_valid_email(email: str) -> bool:
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def refresh_expire():
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=CONFIG.REFRESH_TOKEN_EXPIRE)

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    KST = ZoneInfo("Asia/Seoul")
except Exception as e:
    print("zoneInfo error: ", e)
    # tzdata가 없을 때를 위한 안전한 폴백(고정 +09:00)
    KST = datetime.timezone(datetime.timedelta(hours=9), name="KST")

#
def get_times():
    """# 시간 표시는 전역변수로 두지 말고, 매번 불러서 렌더링해야한다."""
    # 1) 항상 UTC aware부터 시작
    _NOW_TIME_UTC= datetime.datetime.now(datetime.timezone.utc)

    # 2) 필요한 지역시간(KST)으로 변환
    _NOW_TIME = _NOW_TIME_UTC.astimezone(KST)
    return _NOW_TIME_UTC, _NOW_TIME


async def render_with_times(request: Request, template: str, extra_context: dict | None = None):
    now_time_utc, now_time = get_times()
    context = {
        "request": request,
        "now_time_utc": now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f'),
        "now_time": now_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
    }
    if extra_context:
        context.update(extra_context)
    return templates.TemplateResponse(template, context)


######## jinja filter start ################
def to_kst(dt: datetime.datetime | None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    UTC(또는 타임존 정보가 있는) datetime을 KST로 변환해 문자열로 반환합니다.
    - dt가 naive(타임존 없음)이면 UTC로 간주합니다.
    - dt가 None이면 빈 문자열을 반환합니다.
    - fmt로 출력 포맷을 지정할 수 있습니다.
    """
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(KST).strftime(fmt)


def num_format(value):
    return '{:,}'.format(value)


def urlencode_filter(value: str) -> str:
    if value is None:
        return ""
    # 문자열로 변환 후 URL 인코딩
    return urllib.parse.quote_plus(str(value))

######## jinja filter end ################


def create_orm_id(objs_all, user):
    """비동기 함수로 바꿔야 하나???"""
    try:
        unique_num = str(objs_all[0].id + 1)  # 고유해지지만, model.id와 일치하지는 않는다. 삭제된 놈들이 있으면...
    except Exception as e:
        print("c_orm_id Exception error::::::::: 임의로 1로... 할당  ", e)
        unique_num = str(1) # obj가 첫번째 것인 경우: 임의로 1로... 할당
    _random_string = str(uuid.uuid4())
    username = user.username
    orm_id = unique_num + ":" + username + "_" + _random_string
    return orm_id


