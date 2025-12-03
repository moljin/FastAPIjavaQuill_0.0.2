from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Tuple, Sequence

from fastapi import Depends
from sqlalchemy import and_, func, select, or_, delete, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased

from app.core.database import get_db
from app.models.articles import Article, ArticleComment
from app.models.users import User, article_voter
from app.schemas.articles.articles import ArticleIn, ArticleUpdate


class KeysetDirection(StrEnum):
    NEXT = "next"
    PREV = "prev"


@dataclass
class CursorPage:
    items: list[Article]
    has_next: bool
    has_prev: bool
    next_cursor: Optional[str]
    prev_cursor: Optional[str]


def _encode_cursor(ts_iso: str, id_: int) -> str:
    payload = {"ts": ts_iso, "id": id_}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(token: str) -> Tuple[str, int]:
    # URL-safe base64 패딩 보정
    padding = "=" * ((4 - len(token) % 4) % 4)
    raw = base64.urlsafe_b64decode((token + padding).encode("ascii"))
    obj = json.loads(raw.decode("utf-8"))
    return obj["ts"], int(obj["id"])


def _row_to_cursor(row: Article) -> Optional[str]:
    if not row:
        return None
    # created_at은 UTC ISO 문자열로 저장
    ts_iso = row.created_at.isoformat()
    return _encode_cursor(ts_iso, row.id)



def _apply_article_search_filter(stmt, q: Optional[str]):
    if not q:
        return stmt

    pattern = f"%{q.strip()}%"
    comment_user = aliased(User)

    # 조인: 작성자 / 댓글 / 댓글 작성자
    stmt = (
        stmt
        .join(User, User.id == Article.author_id)
        .outerjoin(ArticleComment, ArticleComment.article_id == Article.id)
        .outerjoin(comment_user, comment_user.id == ArticleComment.author_id)
    )

    stmt = stmt.where(
        or_(
            Article.title.ilike(pattern),
            Article.content.ilike(pattern),
            User.username.ilike(pattern),
            ArticleComment.content.ilike(pattern),
            comment_user.username.ilike(pattern),
        )
    )
    return stmt


class ArticleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_article(self, article_in: ArticleIn, user: User, img_path: str = None):
        create_article = Article(**article_in.model_dump())
        author_id = user.id
        create_article.author_id = author_id
        create_article.img_path = img_path

        self.db.add(create_article)
        await self.db.commit()
        await self.db.refresh(create_article)

        return create_article


    async def get_articles(self):
        query = (select(Article).order_by(Article.created_at.desc()))
        result = await self.db.execute(query)
        created_desc_articles = result.scalars().all()
        return created_desc_articles


    async def get_article(self, article_id: int):
        query = (select(Article).where(Article.id == article_id))
        result = await self.db.execute(query)
        article = result.scalar_one_or_none()
        return article


    async def update_article(self, article_id: int, article_update: ArticleUpdate, user: User, img_path: str = None):
        article = await self.get_article(article_id)
        if article is None:
            return None
        if article.author_id != user.id:
            return False

        if img_path is not None:
            article.img_path = img_path
        if article_update.title is not None:
            article.title = article_update.title
        if article_update.content is not None:
            article.content = article_update.content

        await self.db.commit()
        await self.db.refresh(article)
        return article


    async def delete_article(self, article_id: int, user: User):
        article = await self.get_article(article_id)
        if article is None:
            return None
        if article.author_id != user.id:
            return False
        await self.db.delete(article)
        await self.db.commit()
        return True

    # Pagination
    async def count_articles(self, *, query: Optional[str] = None) -> int:
        stmt = select(func.count(distinct(Article.id))).select_from(Article)

        # 이 안에서 ArticleComment 를 join 한다면, 동일 테이블을 또 join 하지 않도록 주의
        stmt = _apply_article_search_filter(stmt, q=query)

        result = await self.db.execute(stmt)

        total = result.scalar_one()
        return int(total or 0)

    async def list_articles_offset(
        self,
        page: int,
        size: int,
        query: Optional[str] = None,
    ) -> tuple[list[Article], int]:

        total = await self.count_articles(query=query)
        if total == 0:
            return [], 0

        start = (page - 1) * size

        # stmt = (
        #     select(Article)
        #     .options(
        #         selectinload(getattr(Article, "author", None)),
        #     )
        #     .order_by(Article.created_at.desc(), Article.id.desc())
        #     .offset(start)
        #     .limit(size)
        # )
        #
        # # 검색 조건 적용
        # stmt = _apply_article_search_filter(stmt, query)
        #
        # result = await self.db.execute(stmt)
        # items: Sequence[Article] = result.scalars().unique().all()
        # 검색 조건이 있을 때는 더 많은 데이터를 가져와서 중복 제거 후 필요한 만큼만 자르기
        if query and query.strip():
            # 중복을 고려하여 더 많은 데이터를 가져옴
            fetch_limit = size * 3  # 보통 이 정도면 충분함
            fetch_offset = max(0, start - size)  # 약간 앞에서부터 가져와서 정확한 페이지네이션 보장
        else:
            fetch_limit = size
            fetch_offset = start

        stmt = (
            select(Article)
            .options(
                selectinload(getattr(Article, "author", None)),
            )
            .order_by(Article.created_at.desc(), Article.id.desc())
            .offset(fetch_offset)
            .limit(fetch_limit)
        )

        # 검색 조건 적용
        stmt = _apply_article_search_filter(stmt, query)

        result = await self.db.execute(stmt)
        all_items: Sequence[Article] = result.scalars().unique().all()

        # 검색이 있는 경우 중복 제거 후 정확한 페이지네이션 적용
        if query and query.strip():
            # 실제 시작 위치 계산 (fetch_offset과 start의 차이 고려)
            actual_start = start - fetch_offset
            items = list(all_items)[actual_start:actual_start + size]
        else:
            items = list(all_items)

        return list(items), total

    # 검색 후 커서 모드 전환을 위한 헬퍼 메서드 추가
    async def get_first_cursor_for_search(self, query: Optional[str] = None) -> Optional[str]:
        """검색 결과의 첫 번째 항목으로부터 커서를 생성"""
        if not query or not query.strip():
            return None

        stmt = (
            select(Article)
            .order_by(Article.created_at.desc(), Article.id.desc())
            .limit(1)
        )

        stmt = _apply_article_search_filter(stmt, query)

        result = await self.db.execute(stmt)
        first_row = result.scalar_one_or_none()

        return _row_to_cursor(first_row) if first_row else None

    async def list_articles_keyset(
            self,
            size: int,
            cursor: Optional[str] = None,
            direction: KeysetDirection = KeysetDirection.NEXT,
            query: Optional[str] = None,
            preserve_search_order: bool = False,  # 새로운 파라미터 추가
    ) -> CursorPage:

        # 검색 시 정렬 순서 조정
        if query and query.strip() and preserve_search_order:
            # 검색 시에는 관련성 기준 정렬 (옵션)
            order_main = [Article.created_at.desc(), Article.id.desc()]
        else:
            # 기본 정렬: created_at DESC, id DESC
            order_main = [Article.created_at.desc(), Article.id.desc()]

        limit = size + 1  # 다음/이전 페이지 존재 확인용

        # 기본 select
        stmt = (
            select(Article)
            .options(
                selectinload(getattr(Article, "author", None)),
                selectinload(getattr(Article, "articlecomments_all", None)),  # 필요 시
            )
        )

        # 우선 검색조건 적용
        stmt = _apply_article_search_filter(stmt, query)

        if cursor:
            ts_iso, cid = _decode_cursor(cursor)
            if direction == KeysetDirection.NEXT:
                # created_at < ts OR (created_at == ts AND id < cid)
                cond = or_(
                    Article.created_at < ts_iso,
                    and_(Article.created_at == ts_iso, Article.id < cid),
                )
                stmt = (
                    stmt
                    .where(cond)
                    .order_by(*order_main)
                    .limit(limit)
                )
            else:
                # PREV: created_at > ts OR (created_at == ts AND id > cid)
                cond = or_(
                    Article.created_at > ts_iso,
                    and_(Article.created_at == ts_iso, Article.id > cid),
                )
                stmt = (
                    stmt
                    .where(cond)
                    .order_by(Article.created_at.asc(), Article.id.asc())
                    .limit(limit)
                )
        else:
            # 커서가 없으면 최초 페이지(NEXT)로 가정
            if direction == KeysetDirection.NEXT:
                stmt = (
                    stmt
                    .order_by(*order_main)
                    .limit(limit)
                )
            else:
                # PREV인데 커서 없음: 정책상 NEXT와 동일하게 시작
                stmt = (
                    stmt
                    .order_by(*order_main)
                    .limit(limit)
                )

        result = await self.db.execute(stmt)
        rows: list[Article] = list(result.scalars().unique().all())

        if direction == KeysetDirection.PREV and rows:
            rows.reverse()

        has_more = len(rows) > size
        if has_more:
            rows = rows[:size]

        first_row = rows[0] if rows else None
        last_row = rows[-1] if rows else None

        next_cursor = _row_to_cursor(last_row) if rows else None
        prev_cursor = _row_to_cursor(first_row) if rows else None

        if direction == KeysetDirection.NEXT:
            has_next = has_more
            has_prev = cursor is not None
        else:
            has_prev = has_more
            has_next = cursor is not None

        return CursorPage(
            items=rows,
            has_next=bool(has_next),
            has_prev=bool(has_prev),
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
        )

    # async def list_articles_keyset(
    #     self,
    #     size: int,
    #     cursor: Optional[str] = None,
    #     direction: KeysetDirection = KeysetDirection.NEXT,
    #     query: Optional[str] = None,
    # ) -> CursorPage:
    #
    #     # 기본 정렬: created_at DESC, id DESC
    #     order_main = [Article.created_at.desc(), Article.id.desc()]
    #     limit = size + 1  # 다음/이전 페이지 존재 확인용
    #
    #     # 기본 select
    #     stmt = (
    #         select(Article)
    #         .options(
    #             selectinload(getattr(Article, "author", None)),
    #             selectinload(getattr(Article, "articlecomments_all", None)),  # 필요 시
    #         )
    #     )
    #
    #     # 우선 검색조건 적용
    #     stmt = _apply_article_search_filter(stmt, query)
    #
    #     if cursor:
    #         ts_iso, cid = _decode_cursor(cursor)
    #         if direction == KeysetDirection.NEXT:
    #             # created_at < ts OR (created_at == ts AND id < cid)
    #             cond = or_(
    #                 Article.created_at < ts_iso,
    #                 and_(Article.created_at == ts_iso, Article.id < cid),
    #             )
    #             stmt = (
    #                 stmt
    #                 .where(cond)
    #                 .order_by(*order_main)
    #                 .limit(limit)
    #             )
    #         else:
    #             # PREV: created_at > ts OR (created_at == ts AND id > cid)
    #             cond = or_(
    #                 Article.created_at > ts_iso,
    #                 and_(Article.created_at == ts_iso, Article.id > cid),
    #             )
    #             stmt = (
    #                 stmt
    #                 .where(cond)
    #                 .order_by(Article.created_at.asc(), Article.id.asc())
    #                 .limit(limit)
    #             )
    #     else:
    #         # 커서가 없으면 최초 페이지(NEXT)로 가정
    #         if direction == KeysetDirection.NEXT:
    #             stmt = (
    #                 stmt
    #                 .order_by(*order_main)
    #                 .limit(limit)
    #             )
    #         else:
    #             # PREV인데 커서 없음: 정책상 NEXT와 동일하게 시작
    #             stmt = (
    #                 stmt
    #                 .order_by(*order_main)
    #                 .limit(limit)
    #             )
    #
    #     result = await self.db.execute(stmt)
    #     rows: list[Article] = list(result.scalars().unique().all())
    #
    #     if direction == KeysetDirection.PREV and rows:
    #         rows.reverse()
    #
    #     has_more = len(rows) > size
    #     if has_more:
    #         rows = rows[:size]
    #
    #     first_row = rows[0] if rows else None
    #     last_row = rows[-1] if rows else None
    #
    #     next_cursor = _row_to_cursor(last_row) if rows else None
    #     prev_cursor = _row_to_cursor(first_row) if rows else None
    #
    #     if direction == KeysetDirection.NEXT:
    #         has_next = has_more
    #         has_prev = cursor is not None
    #     else:
    #         has_prev = has_more
    #         has_next = cursor is not None
    #
    #     return CursorPage(
    #         items=rows,
    #         has_next=bool(has_next),
    #         has_prev=bool(has_prev),
    #         next_cursor=next_cursor,
    #         prev_cursor=prev_cursor,
    #     )


    async def vote_article(self, article_id: int, user: User):
        article = await self.get_article(article_id)
        if article is None:
            return None
        if article.author_id == user.id:
            # (에러 반환으로 수정하자))
            return False

        # 2) 이미 투표했는지 확인
        query = select(article_voter.c.user_id).where(
                and_(article_voter.c.article_id == article_id,
                article_voter.c.user_id == user.id)
            )
        result = await self.db.execute(query)
        exists = result.scalar_one_or_none()
        if exists is not None:
            # 이미 투표했다면 아무 것도 하지 않음(또는 에러 반환으로 수정하자)
            # raise CustomErrorException(status_code=416, detail="이미 '좋아요' 하셨습니다.")
            await self.db.execute(
                delete(article_voter).where(
                    and_(article_voter.c.article_id == article_id,
                         article_voter.c.user_id == user.id, )
                )
            )
            await self.db.commit()
            await self.db.refresh(article) # article을 refresh해도 적용된다. 좋아요 테이블은 객체가 않이라서...
            print("4. exists id: ", exists)
            print("5. vote delete post: ", article.voter_count)
            # return None
            return {"result": "delete", "voter_count": article.voter_count}

        # 3) 직접 연결 테이블에 insert (관계 접근 없음 -> MissingGreenlet 회피)
        await self.db.execute(
            article_voter.insert().values(
                article_id=article_id,
                user_id=user.id,
            )
        )

        await self.db.commit()
        await self.db.refresh(article)
        print("6. vote add post: ", article.voter_count)
        # return True
        return {"result": "insert", "voter_count": article.voter_count}


def get_article_service(db: AsyncSession = Depends(get_db)) -> 'ArticleService':
    return ArticleService(db)

