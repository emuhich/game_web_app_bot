from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pathlib import Path
import random
import httpx

from app.games.honesty.service import HonestyService
from app.users.service import UserService
from app.exceptions import CategoryNotFoundException
from app.config import settings

# Web-фронтенд теперь доступен с корня ("/"), поэтому prefix оставляем пустым
router_webapp = APIRouter(prefix="", tags=["Frontend"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / 'templates'
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


async def _get_user_context(telegram_id: Optional[int]):
    if not telegram_id:
        return {"user": None, "premium": None}
    try:
        user, premium = await UserService.get_profile(telegram_id)
        return {"user": user, "premium": premium}
    except Exception:
        return {"user": None, "premium": None}


@router_webapp.get('/', response_class=HTMLResponse)
async def games_index(request: Request, telegram_id: Optional[int] = None):
    games = [
        {"code": "honesty", "title": "Откровенность", "subtitle": "Поговорим откровенно?", "premium": False, "image": "static/media/honesty.png"}
    ]
    ctx = await _get_user_context(telegram_id)
    return templates.TemplateResponse('index.html', {"request": request, "games": games, **ctx})


@router_webapp.get('/premium', response_class=HTMLResponse)
async def premium_page(request: Request, telegram_id: Optional[int] = None):
    ctx = await _get_user_context(telegram_id)
    return templates.TemplateResponse('premium.html', {"request": request, **ctx, "settings": settings})


@router_webapp.get('/api/premium/invoice', response_class=JSONResponse)
async def get_premium_invoice(telegram_id: int):
    """Создаёт invoice_link через Bot API и возвращает invoice_url для WebApp.openInvoice.

    Сейчас используем Telegram Stars: валюта XTR и тестовая цена 1 звезда.
    Бот по webhook обрабатывает successful_payment и активирует подписку.
    """
    if not settings.BOT_TOKEN:
        raise HTTPException(status_code=500, detail="BOT_TOKEN is not configured")

    api_url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/createInvoiceLink"

    # Жёстко кодируем: 1 год премиума за 1 звезду (XTR)
    payload = {
        "title": "Премиум подписка",
        "description": "1 год доступа ко всем премиум-играм",
        "payload": f"premium_year_{telegram_id}",
        # Для звёзд provider_token не используется, но поле должно существовать
        "provider_token": getattr(settings, "PAYMENTS_PROVIDER_TOKEN", ""),
        "currency": "XTR",  # Telegram Stars
        "prices": [
            {"label": "Подписка", "amount": 1},  # 1 звезда
        ],
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(api_url, json=payload)
    data = resp.json()
    if not data.get("ok"):
        raise HTTPException(status_code=500, detail="Failed to create invoice")

    return {"invoice_url": data["result"]}


@router_webapp.get('/honesty', response_class=HTMLResponse)
async def honesty_categories(request: Request, telegram_id: Optional[int] = None):
    ctx = await _get_user_context(telegram_id)
    categories = await HonestyService.get_visible_categories()
    return templates.TemplateResponse('honesty_categories.html', {"request": request, "categories": categories, **ctx})


@router_webapp.get('/honesty/play/{category_id}', response_class=HTMLResponse)
async def honesty_play(
    request: Request,
    category_id: int,
    telegram_id: Optional[int] = None,
    age_verified: bool = False,
):
    ctx = await _get_user_context(telegram_id)
    try:
        category = await HonestyService.get_category_or_raise(category_id)
    except CategoryNotFoundException:
        raise HTTPException(status_code=404, detail='Категория не найдена')
    if not category.is_visible:
        raise HTTPException(status_code=403, detail='Категория скрыта')
    if category.is_adult and not age_verified:
        return templates.TemplateResponse('gating_age.html', {"request": request, "category": category, **ctx})
    if category.is_premium and not ctx.get('premium'):
        return templates.TemplateResponse('gating_premium.html', {"request": request, "category": category, **ctx})
    questions = await HonestyService.get_questions(category_id)
    if questions:
        random.shuffle(questions)
    return templates.TemplateResponse('honesty_play.html', {"request": request, "category": category, "questions": questions, **ctx})
