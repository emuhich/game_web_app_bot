import asyncio
import logging
import bcrypt
from sqlalchemy import select

from app.config import settings
from app.db.database import async_session_maker
from app.db.models.admin import Admin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def create_or_update_admin():
    """Создаёт администратора из переменных окружения или обновляет пароль, если имя совпадает."""
    username = settings.ADMIN_USERNAME
    raw_password = settings.ADMIN_PASSWORD

    if not username or not raw_password:
        logging.error("ADMIN_USERNAME or ADMIN_PASSWORD is empty in environment")
        return

    # Хэшируем пароль (bcrypt). Повторное хэширование только если пароль изменился.
    async with async_session_maker() as session:
        result = await session.execute(select(Admin).where(Admin.username == username))
        admin = result.scalar_one_or_none()
        hashed = bcrypt.hashpw(raw_password.encode(), bcrypt.gensalt()).decode()

        if admin:
            # Проверяем отличается ли пароль
            if not bcrypt.checkpw(raw_password.encode(), admin.password.encode()):
                admin.password = hashed
                await session.commit()
                logging.info(f"Admin '{username}' password updated.")
            else:
                logging.info(f"Admin '{username}' already exists with same password. Nothing to do.")
        else:
            new_admin = Admin(username=username, password=hashed)
            session.add(new_admin)
            await session.commit()
            logging.info(f"Admin '{username}' created.")


def main():
    asyncio.run(create_or_update_admin())


if __name__ == "__main__":
    main()

