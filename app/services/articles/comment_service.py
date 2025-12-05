from fastapi import Depends
from sqlalchemy import select, and_, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.articles import Article, ArticleComment
from app.models.users import User, articlecomment_voter
from app.schemas.articles.comments import CommentIn
from app.utils.exc_handler import CustomErrorException


class ArticleCommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_comment(self, article: Article, comment_in: CommentIn, user: User):
        create_comment = ArticleComment(**comment_in.model_dump())
        create_comment.article_id = article.id
        create_comment.author_id = user.id

        self.db.add(create_comment)
        await self.db.commit()
        await self.db.refresh(create_comment)

        return create_comment

    async def get_comment(self, comment_id: int):
        query = (select(ArticleComment).where(ArticleComment.id == comment_id))
        result = await self.db.execute(query)
        comment = result.scalar_one_or_none()
        return comment

    async def get_replies_with_paired_comment_id(self, comment_id: int):
        # 댓글의 id가 다른 코멘트의 paired_comment_id(즉, 해당 댓글의 답글(reply)들을 모두 골라낸다.)
        query = (select(ArticleComment).where(ArticleComment.paired_comment_id == comment_id))
        result = await self.db.execute(query)
        replies_with_paired_comment_id = result.scalars().all()
        return replies_with_paired_comment_id

    async def update_comment(self, comment_id: int, comment_in: CommentIn, user: User):
        comment = await self.get_comment(comment_id)
        if comment is None:
            return None
        if comment.author_id != user.id:
            return False
        comment.content = comment_in.content
        await self.db.commit()
        await self.db.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: int, user: User):
        comment = await self.get_comment(comment_id)
        if comment is None:
            return None
        if comment.author_id != user.id:
            return False
        await self.db.delete(comment)
        await self.db.commit()
        return True

    async def vote_comment(self, comment_id: int, user: User):
        comment = await self.get_comment(comment_id)
        if comment is None:
            return None
        if comment.author_id == user.id:
            # (에러 반환으로 수정하자))
            return False

        # 2) 이미 투표했는지 확인
        query = select(articlecomment_voter.c.user_id).where(
                and_(articlecomment_voter.c.articlecomment_id == comment_id,
                     articlecomment_voter.c.user_id == user.id)
            )
        result = await self.db.execute(query)
        exists = result.scalar_one_or_none()
        if exists is not None:
            # 이미 투표했다면 아무 것도 하지 않음(또는 에러 반환으로 수정하자)
            # return None
            # raise CustomErrorException(status_code=416, detail="이미 '좋아요' 하셨습니다.")
            await self.db.execute(
                delete(articlecomment_voter).where(
                    and_(articlecomment_voter.c.articlecomment_id == comment_id,
                         articlecomment_voter.c.user_id == user.id, )
                )
            )
            await self.db.commit()
            await self.db.refresh(comment) # comment를 refresh해도 적용된다. 좋아요 테이블은 객체가 않이라서...
            # return None
            return { "result": "delete", "voter_count": comment.voter_count}

        # 3) 직접 연결 테이블에 insert (관계 접근 없음 -> MissingGreenlet 회피)
        await self.db.execute(
            articlecomment_voter.insert().values(
                articlecomment_id=comment_id,
                user_id=user.id,
            )
        )
        await self.db.commit()
        await self.db.refresh(comment)

        """
        # articlecomment_voter: ArticleComment <-> User 를 잇는 association Table
        query = (select(func.count())
                 .select_from(articlecomment_voter)
                 .where(lambda: articlecomment_voter.c.articlecomment_id == comment_id)) 
        result = await self.db.execute(query)
        count = result.scalar()  # AsyncSession 기준
        print("투표 콜: 새로 추가 후 해당 Comment의 좋아요 갯수: ", count) 
        model에 함수로 넣었다."""

        # return True
        return { "result": "insert", "voter_count": comment.voter_count}


def get_articlecomment_service(db: AsyncSession = Depends(get_db)) -> 'ArticleCommentService':
    return ArticleCommentService(db)