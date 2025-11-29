from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from app.users.dao import UserDAO
from app.bot.keyboards.kbs import app_keyboard
from app.bot.utils.utils import greet_user, get_about_us_text

user_router = Router()


@user_router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    Обрабатывает команду /start.
    """
    existing = await UserDAO.get_by_telegram(message.from_user.id)
    if existing:
        is_new_user = False
        user = existing
    else:
        # Создаём пользователя если не найден
        user = await UserDAO.get_or_create(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username
        )
        is_new_user = True
    await greet_user(message, is_new_user=is_new_user)


@user_router.message(F.text == '🔙 Назад')
async def cmd_back_home(message: Message) -> None:
    """
    Обрабатывает нажатие кнопки "Назад".
    """
    await greet_user(message, is_new_user=False)


@user_router.message(F.text == "ℹ️ О нас")
async def about_us(message: Message):
    kb = app_keyboard(user_id=message.from_user.id, first_name=message.from_user.first_name)
    await message.answer(get_about_us_text(), reply_markup=kb)
