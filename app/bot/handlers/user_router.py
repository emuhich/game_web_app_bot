from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, LabeledPrice, SuccessfulPayment, PreCheckoutQuery

from app.bot.utils.utils import greet_user
from app.config import settings
from app.exceptions import PremiumDurationInvalidException
from app.users.dao import UserDAO
from app.users.service import UserService

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


@user_router.message(Command("test_stars"))
async def cmd_test_stars(message: Message):
    """Тестовый платёж в Telegram Stars: счёт на 1 звезду.

    Помогает проверить, что бот может выставлять инвойсы и что приходят successful_payment.
    """
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title="Пополнение баланса",
        description=f"10 монет",
        provider_token="",  # если используете Telegram Stars, токен провайдера не требуется
        currency="XTR",
        prices=[LabeledPrice(label="1 звезда", amount=1)],  # список цен, amount указывается в минимальных единицах
        payload=f"test_stars_{message.from_user.id}",
        start_parameter="topup-stars"
    )


@user_router.message(F.successful_payment)
async def handle_successful_payment(message: Message) -> None:
    """Логируем успешный платёж и тестово активируем премиум, если payload от премиум-инвойса."""
    sp: SuccessfulPayment = message.successful_payment
    payload = sp.invoice_payload or ""

    # Лог в чат админа, чтобы видеть, что вообще что-то приходит
    try:
        await message.bot.send_message(
            settings.ADMIN_ID,
            f"successful_payment от {message.from_user.id}: payload={payload}, currency={sp.currency}, total={sp.total_amount}",
        )
    except Exception:
        pass

    if payload.startswith("premium_year_"):
        try:
            telegram_id = int(payload.split("premium_year_")[-1])
        except ValueError:
            return

        duration_days = 365
        try:
            await UserService.extend_premium(telegram_id=telegram_id, duration_days=duration_days)
            await message.answer("Премиум успешно активирован! 🎉 Можешь вернуться в игру.")
        except PremiumDurationInvalidException:
            await message.answer("Не удалось активировать премиум: некорректный период.")
        except Exception:
            await message.answer("Не удалось активировать премиум. Попробуй позже.")
    elif payload.startswith("test_stars_"):
        await message.answer("Тестовый платёж в звёздах прошёл успешно! ✨")


@user_router.pre_checkout_query()
async def handle_pre_checkout_query(pcq: PreCheckoutQuery):
    """Обязательный ответ на предварительный запрос оплаты.

    Если не отвечать, платёж зависает на этапе подтверждения.
    """
    try:
        await pcq.bot.answer_pre_checkout_query(pcq.id, ok=True)
    except Exception:
        # Попробуем сообщить пользователю, что что-то пошло не так
        try:
            await pcq.bot.send_message(pcq.from_user.id, "Не удалось подтвердить оплату. Попробуй ещё раз.")
        except Exception:
            pass
