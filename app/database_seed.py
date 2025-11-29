import logging
from sqlalchemy import select
from app.database import async_session_maker
from app.api.models import Master, Service

MASTERS = [
    "Анна",
    "Сергей",
    "Мария",
    "Дмитрий"
]
SERVICES = [
    "Стрижка",
    "Окрашивание",
    "Укладка",
    "Маникюр"
]


async def seed_initial_data():
    async with async_session_maker() as session:
        # Проверяем наличие хотя бы одной записи (быстрее, чем тянуть весь объект)
        masters_exists = await session.scalar(select(Master.master_id).limit(1))
        services_exists = await session.scalar(select(Service.service_id).limit(1))

        if masters_exists and services_exists:
            logging.info("Seed skipped: data already present")
            return

        logging.info("Seeding initial data...")
        try:
            if not masters_exists:
                for name in MASTERS:
                    session.add(Master(master_name=name))
            if not services_exists:
                for name in SERVICES:
                    session.add(Service(service_name=name))
            await session.commit()
            logging.info("Seed completed")
        except Exception as e:
            await session.rollback()
            logging.error(f"Seed error: {e}")
            raise
