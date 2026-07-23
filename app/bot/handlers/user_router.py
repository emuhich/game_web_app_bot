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
        user = await UserDAO.get_or_create(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username
        )
        is_new_user = True
    await greet_user(message, is_new_user=is_new_user)


@user_router.message(F.successful_payment)
async def handle_successful_payment(message: Message) -> None:
    """Логируем успешный платёж и тестово активируем премиум, если payload от премиум-инвойса."""
    sp: SuccessfulPayment = message.successful_payment
    payload = sp.invoice_payload or ""

    # Оплата премиума через классический провайдер (например, YooKassa) — payload начинается с premium_year_
    if payload.startswith("stars_payment_premium_"):
        parts = payload.split("_")
        # ['stars', 'payment', 'premium', '{telegram_id}', '{duration_days}']
        if len(parts) >= 5 and sp.currency == "XTR":
            try:
                telegram_id = int(parts[3])
                duration_days = int(parts[4])
            except ValueError:
                return
            try:
                await UserService.extend_premium(telegram_id=telegram_id, duration_days=duration_days)
                await message.answer("Премиум по оплате в Stars активирован! ✨")
            except PremiumDurationInvalidException:
                await message.answer("Не удалось активировать премиум: некорректный период.")
            except Exception:
                await message.answer("Не удалось активировать премиум. Попробуй позже.")
        else:
            # Неверная валюта или формат payload — игнор
            return
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
        try:
            await pcq.bot.send_message(pcq.from_user.id, "Не удалось подтвердить оплату. Попробуй ещё раз.")
        except Exception:
            pass
