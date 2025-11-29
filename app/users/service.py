from app.users.dao import UserDAO
from app.exceptions import UserNotFoundException, PremiumDurationInvalidException


class UserService:
    @staticmethod
    async def get_profile(telegram_id: int):
        user = await UserDAO.get_by_telegram(telegram_id)
        if not user:
            raise UserNotFoundException()
        premium = await UserDAO.get_active_premium(telegram_id)
        return user, premium

    @staticmethod
    async def extend_premium(telegram_id: int, duration_days: int):
        if duration_days <= 0:
            raise PremiumDurationInvalidException()
        user = await UserDAO.get_by_telegram(telegram_id)
        if not user:
            raise UserNotFoundException()
        return await UserDAO.extend_premium(telegram_id=telegram_id, duration_days=duration_days)

    @staticmethod
    async def toggle_auto_renew(telegram_id: int, enable: bool):
        user = await UserDAO.get_by_telegram(telegram_id)
        if not user:
            raise UserNotFoundException()
        ok = await UserDAO.toggle_auto_renew(telegram_id, enable)
        return ok
