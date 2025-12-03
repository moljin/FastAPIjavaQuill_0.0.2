from typing import Optional

from fastapi import Request, APIRouter, Depends, Form
import random
import ast
import numpy as np
import pandas as pd

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.settings import templates, ADMINS
from app.dependencies.auth import get_optional_current_user, allow_usernames
from app.lottos.models import LottoNum, STATUS
from app.lottos.utils import extract_latest_round, extract_first_win_num, latest_lotto, extract_frequent_num
from app.models.users import User
from app.utils.accounts import is_admin
from app.utils.commons import get_times
from app.utils.exc_handler import CustomErrorException

router = APIRouter()


@router.get("/random")
async def random_lotto(request: Request,
                       num: str = None,
                       db: AsyncSession = Depends(get_db),
                       current_user: Optional[User] = Depends(get_optional_current_user)):

    old_latest = await latest_lotto(db)

    if old_latest:
        latest_round_num = old_latest.latest_round_num
        if num:
            if int(num) < 6:
                message = f"6이상의 숫자를 입력하세요! 우선 빈도에 관계없이 무작위로 추출했어요!"
                now_time_utc, now_time = get_times()
                _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
                _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')
                context = {"variable": sorted(random.sample(range(1, 46), 6)),
                           "latest": int(latest_round_num),
                           "message": message,
                           'current_user': current_user,
                           "now_time_utc": _NOW_TIME_UTC,
                           "now_time": _NOW_TIME,
                           'admin': is_admin(current_user)}
                return templates.TemplateResponse(
                    request=request,
                    name="lottos/lotto.html",
                    context=context
                )
            elif int(num) >= 45:
                message = f"45이상은 빈도에 관계없이 무작위로 추출하는 것과 같아요!"
                now_time_utc, now_time = get_times()
                _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
                _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')
                context = {"variable": sorted(random.sample(range(1, 46), 6)),
                           "latest": int(latest_round_num),
                           "message": message,
                           'current_user': current_user,
                           "now_time_utc": _NOW_TIME_UTC,
                           "now_time": _NOW_TIME,
                           'admin': is_admin(current_user)}
                return templates.TemplateResponse(
                    request=request,
                    name="lottos/lotto.html",
                    context=context
                )
            else:
                lotto_num_list = ast.literal_eval(old_latest.lotto_num_list)
                wanted_top_list, lotto_random_num = await extract_frequent_num(lotto_num_list, int(num))
                message = f"당첨 빈도가 높은 번호 {num}개중 6개를 무작위로 추출"
                now_time_utc, now_time = get_times()
                _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
                _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')
                context = {"input_num": num,
                           "variable": lotto_random_num,
                           "latest": int(latest_round_num),
                           "message": message,
                           'current_user': current_user,
                           "now_time_utc": _NOW_TIME_UTC,
                           "now_time": _NOW_TIME,
                           'admin': is_admin(current_user)}
                return templates.TemplateResponse(
                    request=request,
                    name="lottos/lotto.html",
                    context=context
                )

        message = f"당첨 빈도에 관계없이 6개의 숫자를 무작위로 추출"
        now_time_utc, now_time = get_times()
        _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
        _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')
        context = {"variable": sorted(random.sample(range(1, 46), 6)),
                   "latest": latest_round_num,
                   "message": message,
                   'current_user': current_user,
                   "now_time_utc": _NOW_TIME_UTC,
                   "now_time": _NOW_TIME,
                   'admin': is_admin(current_user)}
        return templates.TemplateResponse(
            request=request,
            name="lottos/lotto.html",
            context=context
        )
    else:
        message = f"당첨 빈도에 관계없이 6개의 숫자를 무작위로 추출"
        now_time_utc, now_time = get_times()
        _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
        _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')
        context = {"variable": sorted(random.sample(range(1, 46), 6)),
                   "latest": "0000",
                   "message": message,
                   'current_user': current_user,
                   "now_time_utc": _NOW_TIME_UTC,
                   "now_time": _NOW_TIME,
                   'admin': is_admin(current_user)}
        return templates.TemplateResponse(
            request=request,
            name="lottos/lotto.html",
            context=context
        )


"""# TOP10으로 로또번호를 추출하는 함수"""
@router.get("/top10")
async def top10_lotto(request: Request,
                      num: str = None,
                      db: AsyncSession = Depends(get_db),
                      current_user: Optional[User] = Depends(get_optional_current_user)):
    old_latest = await latest_lotto(db)
    if num:
        print("num: ", num)
        lotto_num_list = ast.literal_eval(old_latest.lotto_num_list)
        latest_round_num = old_latest.latest_round_num
        wanted_top_list, lotto_random_num = await extract_frequent_num(lotto_num_list, int(num))
        message = f"당첨 빈도가 높은 번호 {num}개중 6개를 무작위로 추출"
        now_time_utc, now_time = get_times()
        _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
        _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')
        context = {"variable": lotto_random_num,
                   "latest": int(latest_round_num),
                   "message": message,
                   'current_user': current_user,
                   "now_time_utc": _NOW_TIME_UTC,
                   "now_time": _NOW_TIME,
                   'admin': is_admin(current_user)
                   }
        return templates.TemplateResponse(
            request=request,
            name="lottos/lotto.html",
            context=context
        )
    if old_latest:
        latest_round_num = old_latest.latest_round_num
        """string 로 저장된 최다빈도 번호를 integer list 로 다시 변환하고, 번호 6개 무작위 추출"""
        lotto_top10 = ast.literal_eval(old_latest.extract_num)
        lotto_random_num = sorted(random.sample(lotto_top10, 6))
    else:
        latest_round_num = 1193
        lotto_top10 = [34, 12, 13, 18, 27, 14, 40, 45, 33, 37]
        lotto_random_num = sorted(random.sample(lotto_top10, 6))
    message = f"당첨 빈도가 높은 번호 10개중 6개를 무작위로 추출"
    now_time_utc, now_time = get_times()
    _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
    _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')
    context = {"variable": lotto_random_num,
               "latest": int(latest_round_num),
               "message": message,
               'current_user': current_user,
               "now_time_utc": _NOW_TIME_UTC,
               "now_time": _NOW_TIME,
                   'admin': is_admin(current_user)
               }
    return templates.TemplateResponse(
        request=request,
        name="lottos/lotto.html",
        context=context
    )


@router.get("/win/extract")
async def win_extract_lotto(request: Request,
                            db: AsyncSession = Depends(get_db),
                            current_user: Optional[User] = Depends(get_optional_current_user)
                            ):
    old_latest = await latest_lotto(db)
    if old_latest:
        '''string 로 저장된 최다빈도 번호를 integer list 로 다시 변환'''
        full_int_list = ast.literal_eval(old_latest.extract_num)
    else:
        full_int_list = []

    now_time_utc, now_time = get_times()
    _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
    _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')

    context = {"old_extract": old_latest,
               "old_extract_num": full_int_list,
               'current_user': current_user,
               "now_time_utc": _NOW_TIME_UTC,
               "now_time": _NOW_TIME,
               'admin': is_admin(current_user)
               }
    return templates.TemplateResponse(
        request=request,
        name="lottos/extract.html",
        context=context
    )


@router.post("/win/top10/post")
async def lotto_top10_post(request: Request,
                           latest_round: str = Form(...),
                           db: AsyncSession = Depends(get_db),
                           admin_user = Depends(allow_usernames(ADMINS))
                           ):
    print("admin_user: ", admin_user.username)
    print(f"latest_round: {latest_round}")
    old_latest = await latest_lotto(db) # db에 저장된 것
    latest_page = await extract_latest_round() # 로또사이트의 마지막 회차
    if old_latest:
        if old_latest.latest_round_num == latest_page:
            if latest_round == latest_page:
                raise CustomErrorException(status_code=499, detail="Conflict")
            elif int(latest_round) > int(old_latest.latest_round_num):
                raise CustomErrorException(status_code=499, detail="No Event")

    if int(latest_round) == int(latest_page):
        lotto_num_list, top10_list = await extract_first_win_num(db)
        if old_latest:
            old_latest.status = STATUS[0]
            db.add(old_latest)
            await db.commit()
            await db.refresh(old_latest)

        new = LottoNum()
        new.title = latest_page + "회차"
        new.latest_round_num = latest_page
        new.extract_num = str(top10_list)  # map_str_extract_num
        new.lotto_num_list = str(lotto_num_list)
        db.add(new)
        await db.commit()
        await db.refresh(new)

        """string 로 저장된 최다빈도 번호를 integer list 로 다시 변환"""
        from typing import cast
        extract_num = cast(str, new.extract_num) # type(extract_num) str
        new_extract_num = ast.literal_eval(extract_num) # type(new_extract_num) list

        # "current_user": admin_user 이것을 넘길 때, jsonable_encoder : from . import v2에러가 발생한다.
        # admin_user는 user를 반환해서 사용할 수 있는데, 왜 에러가 난거지?
        return {"latest": str(latest_page), "top10_list": str(top10_list)}
    else:
        print("입력하신 회차는 마지막 회차가 아니에요...")
        raise CustomErrorException(status_code=415, detail="Not Last")