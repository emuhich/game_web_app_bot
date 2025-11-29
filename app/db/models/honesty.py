from sqlalchemy import String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.db.database import Base


class HonCategory(Base):
    __tablename__ = 'honesty_categories'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    image: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, index=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_adult: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    questions: Mapped[list['HonQuestion']] = relationship(
        back_populates='category', cascade='all, delete-orphan'
    )

    @property
    def upload_image(self):
        return None

    def __str__(self) -> str:
        return self.name or f"Category #{self.id}"


class HonQuestion(Base):
    __tablename__ = 'honesty_questions'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('honesty_categories.id', ondelete='CASCADE'),
                                             index=True)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped['HonCategory'] = relationship(back_populates='questions')

    def __str__(self) -> str:
        preview = (self.text or '').strip()
        return preview[:50] + ('...' if len(preview) > 50 else '')
