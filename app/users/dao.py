from typing import Optional, Sequence
from datetime import date, timedelta
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.dao.base import BaseDAO
from app.db.models.users import User, Premium
import app.db.database as db


class UserDAO(BaseDAO):
    model = User

    @classmethod
    async def get_by_telegram(cls, telegram_id: int) -> Optional[User]:
        async with db.async_session_maker() as session:
            result = await session.execute(select(User).filter_by(telegram_id=telegram_id))
            return result.scalar_one_or_none()

    @classmethod
    async def get_or_create(cls, telegram_id: int, first_name: str, username: Optional[str] = None) -> User:
        async with db.async_session_maker() as session:
            result = await session.execute(select(User).filter_by(telegram_id=telegram_id))
            user = result.scalar_one_or_none()
            if user:
                return user
            user = User(telegram_id=telegram_id, first_name=first_name, username=username)
            session.add(user)
            try:
                await session.commit()
                await session.refresh(user)
            except SQLAlchemyError:
                await session.rollback()
                raise
            return user

    @classmethod
    async def update_username(cls, telegram_id: int, username: str) -> bool:
        async with db.async_session_maker() as session:
            try:
                await session.execute(update(User).where(User.telegram_id == telegram_id).values(username=username))
                await session.commit()
                return True
            except SQLAlchemyError:
                await session.rollback()
                return False

    @classmethod
    async def deactivate(cls, telegram_id: int) -> bool:
        async with db.async_session_maker() as session:
            try:
                await session.execute(update(User).where(User.telegram_id == telegram_id).values(is_active=False))
                await session.commit()
                return True
            except SQLAlchemyError:
                await session.rollback()
                return False

    @classmethod
    async def list_active(cls, limit: int = 100, offset: int = 0) -> Sequence[User]:
        async with db.async_session_maker() as session:
            result = await session.execute(
                select(User).filter_by(is_active=True).order_by(User.telegram_id).limit(limit).offset(offset)
            )
            return result.scalars().all()

    # ---------------- Premium -----------------
    @classmethod
    async def get_active_premium(cls, telegram_id: int) -> Optional[Premium]:
        today = date.today()
        async with db.async_session_maker() as session:
            result = await session.execute(select(Premium).filter_by(user_id=telegram_id))
            premium = result.scalar_one_or_none()
            if premium and premium.expire_date >= today:
                return premium
            return None

    @classmethod
    async def extend_premium(cls, telegram_id: int, duration_days: int) -> Premium:
        if duration_days <= 0:
            raise ValueError("duration_days must be > 0")
        today = date.today()
        async with db.async_session_maker() as session:
            result = await session.execute(select(Premium).filter_by(user_id=telegram_id))
            premium = result.scalar_one_or_none()
            if premium:
                base_date = premium.expire_date if premium.expire_date >= today else today
                premium.expire_date = base_date + timedelta(days=duration_days)
                premium.purchase_date = today
            else:
                premium = Premium(
                    user_id=telegram_id,
                    purchase_date=today,
                    expire_date=today + timedelta(days=duration_days)
                )
                session.add(premium)
            try:
                await session.commit()
                await session.refresh(premium)
            except SQLAlchemyError:
                await session.rollback()
                raise
            return premium

    @classmethod
    async def toggle_auto_renew(cls, telegram_id: int, enable: bool) -> bool:
        async with db.async_session_maker() as session:
            result = await session.execute(select(Premium).filter_by(user_id=telegram_id))
            premium = result.scalar_one_or_none()
            if not premium:
                return False
            premium.auto_renew = enable
            try:
                await session.commit()
                return True
            except SQLAlchemyError:
                await session.rollback()
                return False
