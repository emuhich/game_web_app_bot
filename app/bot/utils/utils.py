from aiogram.types import Message
from app.bot.keyboards.kbs import main_keyboard


async def greet_user(message: Message, is_new_user: bool) -> None:
    """Приветствует пользователя и отправляет соответствующее сообщение."""
    greeting = "Добро пожаловать" if is_new_user else "С возвращением"
    status = "Вы успешно зарегистрированы!" if is_new_user else "Рады видеть вас снова!"
    await message.answer(
        f"{greeting}, <b>{message.from_user.full_name}</b>! {status}\n"
        "Мини-игры для пар и компаний 🎮 — вопросы, задания и весёлые челленджи, "
        "чтобы лучше узнать друг друга 💬🔥",
        reply_markup=main_keyboard(),
    )
