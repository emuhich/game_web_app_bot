from aiogram.types import ReplyKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.config import settings


def main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    url_applications = f"{settings.BASE_SITE}/"
    keyboard.button(text="Играть", web_app=WebAppInfo(url=url_applications))
    return keyboard.adjust(1).as_markup()
