from typing import Optional

from sqlalchemy import String, Boolean, Table, Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import BaseModel, Base


class User(BaseModel):
    __tablename__ = "users"

    # String은 제한 글자수를 지정해야 한다.
    username: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    img_path: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

"""
- unique 와 index 중복
    - unique=True만으로도 고유 인덱스가 생성됩니다. index=True는 중복이므로 제거해도 됩니다(권장).
- 비밀번호 길이
    - password는 해시를 저장하므로 길이를 넉넉히 두는 것이 안전합니다(예: String(255)). 해시 종류에 따라 100자를 넘길 수 있습니다.
- 기본 키/타입
    - id는 Integer(primary_key=True)면 충분합니다. 아주 큰 규모를 예상하면 BigInteger도 고려할 수 있습니다.
"""

article_voter = Table('article_voters',
                       Base.metadata,
                       Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
                       Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
                       # 중복 등록 방지(복합 PK로 이미 보장되지만, 이름 있는 제약 예시)
                       UniqueConstraint("user_id", "article_id", name="uq_article_voters")
                       )


articlecomment_voter = Table('articlecomment_voters',
                     Base.metadata,
                     Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
                     Column('articlecomment_id', Integer, ForeignKey('article_comments.id'), primary_key=True),
                     # 중복 등록 방지(복합 PK로 이미 보장되지만, 이름 있는 제약 예시)
                     UniqueConstraint("user_id", "articlecomment_id", name="uq_articlecomment_voters")
                     )