from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.dao.base import BaseDAO
from app.db.models.honesty import HonCategory, HonQuestion
import app.db.database as db


class HonCategoryDAO(BaseDAO):
    model = HonCategory

    @classmethod
    async def get_visible(cls) -> List[HonCategory]:
        async with db.async_session_maker() as session:
            stmt = (
                select(HonCategory)
                .options(selectinload(HonCategory.questions))
                .filter_by(is_visible=True)
                .order_by(HonCategory.order)
            )
            result = await session.execute(stmt)
            return result.scalars().unique().all()

    @classmethod
    async def get_by_id(cls, category_id: int) -> Optional[HonCategory]:
        async with db.async_session_maker() as session:
            stmt = select(HonCategory).options(selectinload(HonCategory.questions)).filter_by(id=category_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()


class HonQuestionDAO(BaseDAO):
    model = HonQuestion

    @classmethod
    async def get_by_category(cls, category_id: int) -> List[HonQuestion]:
        async with db.async_session_maker() as session:
            result = await session.execute(
                select(HonQuestion).filter_by(category_id=category_id)
            )
            return result.scalars().all()

    @classmethod
    async def add_question(cls, category_id: int, text: str) -> HonQuestion:
        async with db.async_session_maker() as session:
            question = HonQuestion(category_id=category_id, text=text)
            session.add(question)
            try:
                await session.commit()
                await session.refresh(question)
            except SQLAlchemyError:
                await session.rollback()
                raise
            return question
