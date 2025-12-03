from typing import Optional

from sqlalchemy import Integer, String, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import BaseModel

STATUS = ('old', 'latest')


class LottoNum(BaseModel):
    __tablename__ = 'lottos'

    title: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=STATUS[1], nullable=False)
    latest_round_num: Mapped[str] = mapped_column(String(100), nullable=False)
    extract_num: Mapped[str] = mapped_column(String(100), nullable=False)
    lotto_num_list: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<LottoNum(id={self.id}, email='{self.title}')>"