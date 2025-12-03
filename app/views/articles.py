import math
from typing import List, Optional
from urllib.parse import quote_plus

from fastapi import APIRouter, Request, Depends, HTTPException, status, Response, Query
from fastapi.responses import HTMLResponse

from app.core.settings import templates
from app.dependencies.auth import get_current_user, get_optional_current_user
from app.models.users import User
from app.services.articles.article_service import ArticleService, get_article_service, KeysetDirection
from app.utils.commons import render_with_times, get_times
from app.schemas.articles import articles as schema_article

router = APIRouter()


@router.get("/article/create")
async def create(request: Request,
                   current_user: User = Depends(get_current_user)):
    extra = {
        "current_user": current_user,
        "mark_id": 0
    }
    return await render_with_times(request, "articles/create.html", extra)


DEEP_PAGE_THRESHOLD = 100  # 얕은 범위까지만 오프셋, 이후는 커서 모드 권장
"""설정된 값의 페이지 이후부터 prev(화살표), next(화살표)를 누르면 커서 모드로 넘어간다.
계속 페이지 번호를 누르면, 설정된 값 이후로 넘어 가더라도 오프셋 모드는 유지된다.
게시물 100개 만들어 놓고, DEEP_PAGE_THRESHOLD = 8로 해놓으면, 9페이지부터 다음 화살표를 누르면 커서모드로 간다.
(.venv) PS D:\Python_FastAPI\My_Advanced\FastAPIjavaQuill_0.0.1> python
Python 3.13.5 (tags/v3.13.5:6cb20a2, Jun 11 2025, 16:15:46) [MSC v.1943 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> from app.core.database import AsyncSessionLocal
>>> from app.models.articles import Article
>>> from datetime import datetime
>>> from datetime import timezone
>>> import asyncio
>>> db = AsyncSessionLocal()
>>> for i in range(300):
...     q = Article(title='테스트 데이터입니다.', content='내용무', author_id=1, created_at=datetime.now(timezone.utc))
...     db.add(q)
>>> asyncio.run(db.commit())
"""
@router.get("/all",
            response_model=List[schema_article.ArticleOut],
            summary="게시물 목록 조회",
            description="전체 게시물 목록을 최신순으로 조회합니다.",
            responses={404: {
                "description": "게시글 조회 실패",
                "content": {"application/json": {"example": {"detail": "등록된 게시물들을 찾을 수 없습니다."}}}
            }})
async def get_articles(request: Request,
                       article_service: ArticleService = Depends(get_article_service),
                       current_user: Optional[User] = Depends(get_optional_current_user),
                       # 오프셋용
                       page: int = Query(1, ge=1, description="현재 페이지 (1부터 시작)"),
                       size: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
                       # 커서용
                       mode: str = Query("auto", pattern="^(auto|offset|cursor)$"),
                       cursor: Optional[str] = Query(None, description="커서 토큰"),
                       _dir: str = Query("next", pattern="^(next|prev)$"),
                       approx_page: Optional[int] = Query(None, description="커서 모드에서의 대략적 페이지"),
                       # 추가: 검색어
                       query: Optional[str] = Query(None, description="검색어 (제목/내용/작성자/댓글내용/댓글작성자)"),
                       ):

    # 공통: 전체 개수
    total_count = await article_service.count_articles(query=query)
    if total_count == 0:
        if query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f'"{query}"라는 검색어가 포함된 게시물이 없습니다.'
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="등록된 게시물이 없습니다."
        )
    total_pages = max(1, math.ceil(total_count / size))

    # 전략 결정
    # using_cursor = False
    direction = KeysetDirection.NEXT if _dir == "next" else KeysetDirection.PREV

    if mode == "cursor" or (mode == "auto" and cursor is not None):
        using_cursor = True
    elif mode == "offset":
        using_cursor = False
    else:
        # auto: cursor가 없고, 얕은 페이지면 offset, 깊으면 offset이지만 다음 링크에서 cursor 전환
        using_cursor = False

    # 1) 커서 모드
    if using_cursor:
        # approx_page가 없으면 임계 지점 또는 1로 초기화
        if approx_page is None:
            # 임계 이상에서 커서 시작했다고 가정
            approx_page = min(max(page, 1), total_pages)
            if approx_page < DEEP_PAGE_THRESHOLD:
                approx_page = DEEP_PAGE_THRESHOLD

        cpage = await article_service.list_articles_keyset(
            size=size, cursor=cursor, direction=direction, query=query,
        )

        all_articles = cpage.items

        # Prev/Next 링크 구성
        # - 커서 모드에서 Prev를 누를 때 approx_page-1
        # - approx_page-1이 임계 이하가 되면 Prev를 오프셋 링크로 복귀
        has_prev = cpage.has_prev
        has_next = cpage.has_next

        prev_href = None
        next_href = None

        # Prev
        if has_prev:
            prev_approx = max(1, approx_page - 1)
            if prev_approx < DEEP_PAGE_THRESHOLD:
                # 오프셋으로 복귀
                # 검색어가 있으면 함께 전달
                if query:
                    prev_href = (
                        f"?page={DEEP_PAGE_THRESHOLD - 1}"
                        f"&size={size}"
                        f"&mode=offset"
                        f"&query={quote_plus(query)}"
                    )
                else:
                    prev_href = (
                        f"?page={DEEP_PAGE_THRESHOLD - 1}"
                        f"&size={size}"
                        f"&mode=offset"
                    )
            else:
                # 커서 모드 Prev 링크에 검색어 포함
                if query:
                    prev_href = (
                        f"?mode=cursor"
                        f"&size={size}"
                        f"&cursor={cpage.prev_cursor}"
                        f"&dir=prev"
                        f"&approx_page={prev_approx}"
                        f"&query={quote_plus(query)}"
                    )
                else:
                    prev_href = (
                        f"?mode=cursor"
                        f"&size={size}"
                        f"&cursor={cpage.prev_cursor}"
                        f"&dir=prev"
                        f"&approx_page={prev_approx}"
                    )

        # Next
        if has_next:
            next_approx = min(total_pages, approx_page + 1)
            # 커서 모드 Next 링크에 검색어 포함
            if query:
                next_href = (
                    f"?mode=cursor"
                    f"&size={size}"
                    f"&cursor={cpage.next_cursor}"
                    f"&dir=next"
                    f"&approx_page={next_approx}"
                    f"&query={quote_plus(query)}"
                )
            else:
                next_href = (
                    f"?mode=cursor"
                    f"&size={size}"
                    f"&cursor={cpage.next_cursor}"
                    f"&dir=next"
                    f"&approx_page={next_approx}"
                )

            # 페이지네이션 컨텍스트(커서 모드)
        pagination = {
            "mode": "cursor",
            "size": size,
            "total_count": total_count,
            "total_pages": total_pages,
            "approx_page": approx_page,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_href": prev_href,
            "next_href": next_href,
            "query": query,
        }

        now_time_utc, now_time = get_times()
        _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
        _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')

        context = {
            "now_time_utc": _NOW_TIME_UTC,
            "now_time": _NOW_TIME,
            "all_articles": all_articles,
            "current_user": current_user,
            "pagination": pagination,
            "query": query,
        }

        return templates.TemplateResponse(
            request=request, name="articles/articles.html", context=context
        )

    # 2) 오프셋 모드
    # 페이지 보정
    if page > total_pages:
        page = total_pages
    if page < 1:
        page = 1

    items, _ = await article_service.list_articles_offset(page=page, size=size, query=query,)
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="등록된 게시물이 없습니다."
        )

    # 기존 스타일의 숫자 페이지
    has_prev = page > 1
    has_next = page < total_pages

    # 임계 페이지에서 다음 클릭 시 커서 모드로 다리 놓기
    # 현재 페이지의 마지막 아이템으로 next_cursor 생성해서 next 링크로 사용
    next_href = None
    prev_href = None

    if has_prev:
        # 오프셋 Prev 링크에 검색어 포함
        if query:
            prev_href = (
                f"?page={page - 1}"
                f"&size={size}"
                f"&mode=offset"
                f"&query={quote_plus(query)}"
            )
        else:
            prev_href = f"?page={page - 1}&size={size}&mode=offset"

    if has_next:
        if page >= DEEP_PAGE_THRESHOLD:
            # 커서 모드로 전환: 현재 페이지 마지막 아이템 기준 next_cursor 생성
            from app.services.articles.article_service import _row_to_cursor
            bridge_cursor = _row_to_cursor(items[-1])
            # 커서 모드 브리지 링크에 검색어 포함
            if query:
                next_href = (
                    f"?mode=cursor"
                    f"&size={size}"
                    f"&cursor={bridge_cursor}"
                    f"&dir=next"
                    f"&approx_page={min(total_pages, page + 1)}"
                    f"&query={quote_plus(query)}"
                )
            else:
                next_href = (
                    f"?mode=cursor"
                    f"&size={size}"
                    f"&cursor={bridge_cursor}"
                    f"&dir=next"
                    f"&approx_page={min(total_pages, page + 1)}"
                )
        else:
            # 오프셋 Next 링크에 검색어 포함
            if query:
                next_href = (
                    f"?page={page + 1}"
                    f"&size={size}"
                    f"&mode=offset"
                    f"&query={quote_plus(query)}"
                )
            else:
                next_href = f"?page={page + 1}&size={size}&mode=offset"

    # # 현재 페이지 기준 좌우 2개씩 번호 노출
    page_range = list(range(max(1, page - 2), min(total_pages, page + 2) + 1))
    # # 현재 페이지 기준 좌우 5개씩 번호 노출 (총 10개 + 현재 페이지)
    # page_range = list(range(max(1, page - 5), min(total_pages, page + 5) + 1))

    # 10개 단위 페이지네이션
    # PAGE_BLOCK_SIZE = 5
    # start_page = ((page - 1) // PAGE_BLOCK_SIZE) * PAGE_BLOCK_SIZE + 1
    # end_page = min(start_page + PAGE_BLOCK_SIZE - 1, total_pages)
    # page_range = list(range(start_page, end_page + 1))
    # page_range = list(range(max(1, page - 2), min(total_pages, page + 2) + 1))

    pagination = {
        "mode": "offset",
        "page": page,
        "size": size,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_prev": has_prev,
        "has_next": has_next,
        "prev_page": page - 1 if has_prev else None,
        "next_page": page + 1 if has_next else None,
        "prev_href": prev_href,
        "next_href": next_href,
        "page_range": page_range,
        "deep_page_threshold": DEEP_PAGE_THRESHOLD,
        "query": query,
    }

    now_time_utc, now_time = get_times()
    _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
    _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')

    context = {
        "now_time_utc": _NOW_TIME_UTC,
        "now_time": _NOW_TIME,
        "all_articles": items,
        "current_user": current_user,
        "pagination": pagination,
        "query": query,
    }

    return templates.TemplateResponse(
        request=request, name="articles/articles.html", context=context
    )

    # '''
    # total_count = await article_service.count_articles()
    # if total_count == 0:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND, detail="등록된 게시물이 없습니다."
    #     )
    #
    # articles = await article_service.get_articles()
    # extra = {
    #     "current_user": current_user,
    #     "articles": articles,
    # }
    # return await render_with_times(request, "articles/articles.html", extra)'''


@router.get("/article/{article_id}",
            summary="특정 게시글 조회", description=" 게시글 ID 기반으로 특정 게시물을 조회합니다.",
            responses={404: {
                "description": "게시글 조회 실패",
                "content": {"application/json": {"example": {"detail": "게시글을 찾을 수 없습니다."}}}
            }})
async def get_article(request: Request, article_id: int,
                      article_service: ArticleService = Depends(get_article_service),
                      current_user: Optional[User] = Depends(get_optional_current_user)):
    article = await article_service.get_article(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 게시글을 찾을 수 없습니다."
        )

    reply_objs = list() # comment단 reply 골라 내기
    for comment in article.articlecomments_all:
        if comment.paired_comment_id:
            reply_objs.append(comment)
    print("reply_objs:", reply_objs)
    extra = {
        "current_user": current_user,
        "article": article,
        "reply_objs": reply_objs,
        "mark_id": 0,
    }
    return await render_with_times(request, "articles/detail.html", extra)

@router.get("/article/update/{article_id}", response_class=HTMLResponse,
            summary="게시글 수정 페이지 HTMLResponse", description="게시글 수정 페이지 templates.TemplateResponse")
async def update(request: Request, response: Response,
                            article_id: int,
                            article_service: ArticleService = Depends(get_article_service),
                            current_user: User = Depends(get_current_user)):
    article = await article_service.get_article(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: 로그인하지 않았습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        user_id = current_user.id
        if user_id != article.author_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: 접근 권한이 없습니다."
            )
    extra = {
        "current_user": current_user,
        "article": article,
        "mark_id": 0
    }
    return await render_with_times(request, "articles/create.html", extra)