from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, LabeledPrice, SuccessfulPayment
from app.users.dao import UserDAO
from app.bot.keyboards.kbs import app_keyboard
from app.bot.utils.utils import greet_user, get_about_us_text
from app.config import settings
from app.users.service import UserService
from app.exceptions import PremiumDurationInvalidException

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


@user_router.message(Command("test_stars"))
async def cmd_test_stars(message: Message):
    """Тестовый платёж в Telegram Stars: счёт на 1 звезду.

    Помогает проверить, что бот может выставлять инвойсы и что приходят successful_payment.
    """
    prices = [LabeledPrice(label="Тестовая подписка", amount=1)]  # 1 звезда
    try:
        await message.answer_invoice(
            title="Тестовый платёж (звёзды)",
            description="Проверка оплаты Telegram Stars",
            payload=f"test_stars_{message.from_user.id}",
            provider_token=getattr(settings, "PAYMENTS_PROVIDER_TOKEN", ""),
            currency="XTR",
            prices=prices,
        )
    except Exception as e:
        # логируем в личку админа и в чат
        try:
            await message.bot.send_message(settings.ADMIN_ID, f"Ошибка answer_invoice: {e}")
        except Exception:
            pass
        await message.answer(f"Не удалось отправить тестовый инвойс: {e}")


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
