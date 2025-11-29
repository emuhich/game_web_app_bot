from sqlalchemy import select, insert, update, delete

import app.db.database as db


class BaseDAO:
    model = type[db.Base]

    @classmethod
    async def get_by_id(cls, model_id):
        async with db.async_session_maker() as session:
            query = select(cls.model).filter_by(id=model_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_one_or_none(cls, **filters):
        async with db.async_session_maker() as session:
            query = select(cls.model).filter_by(**filters)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_all(cls, **filters):
        async with db.async_session_maker() as session:
            query = select(cls.model.__table__.columns).filter_by(**filters)
            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def create(cls, **kwargs):
        async with db.async_session_maker() as session:
            query = insert(cls.model).values(**kwargs)
            await session.execute(query)
            await session.commit()

    @classmethod
    async def add(cls, **kwargs):
        """Create ORM instance and return it refreshed."""
        async with db.async_session_maker() as session:
            obj = cls.model(**kwargs)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj

    @classmethod
    async def update(cls, model_id: int, **kwargs):
        async with db.async_session_maker() as session:
            query = update(cls.model).where(cls.model.id == model_id).values(**kwargs)
            await session.execute(query)
            await session.commit()

    @classmethod
    async def delete(cls, model_id: int):
        async with db.async_session_maker() as session:
            query = delete(cls.model).where(cls.model.id == model_id)
            await session.execute(query)
            await session.commit()
