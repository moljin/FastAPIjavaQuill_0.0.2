from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, ConfigDict
from pydantic_core import PydanticCustomError

from app.schemas.accounts import UserOrm


class CommentIn(BaseModel):
    # paired_comment_id: reply Comment 들어 올때 사용 (ArticleComment 모델과 같은 이름으로...)
    paired_comment_id: int | None = None
    content: str

    @field_validator('content')
    def not_empty(cls, v):
        if not v or not v.strip():
            # 'msg': 'Value error, 빈 값은 허용되지 않습니다.' 이렇게 프론트로 넘어간다.
            # raise ValueError('빈 값은 허용되지 않습니다.')
            # 접두사 없이 메시지 그대로 내려감
            raise PydanticCustomError('empty_value', '빈 값은 허용되지 않습니다.')

        return v


class CommentOut(BaseModel):
    id: int
    content: str | None = None
    created_at: datetime
    updated_at: datetime
    author: Optional[UserOrm] = None
    article_id: int
    voter: list[UserOrm] = []
    model_config = ConfigDict(from_attributes=True)

    """
    - model_config = ConfigDict(from_attributes=True)의 의미
        - Pydantic v2 방식입니다.
        - 딕셔너리(dict) 같은 매핑 타입뿐 아니라, ORM 인스턴스나 일반 파이썬 객체처럼 “속성 접근”으로 값을 꺼내는 객체로부터 모델을 생성/검증하도록 허용합니다.
        - 즉, SQLAlchemy 모델 인스턴스 같은 객체를 QuestionOut.model_validate(obj)로 바로 검증/직렬화할 수 있게 해줍니다.

    - class Config: orm_mode = True는 올바른가?
        - Pydantic v1에서 쓰던 방식으로, v2에서는 권장되지 않으며 무시되거나 동작하지 않습니다.
        - v2에서는 model_config = ConfigDict(from_attributes=True)로 대체해야 합니다.
    """