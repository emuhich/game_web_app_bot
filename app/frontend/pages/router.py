from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pathlib import Path
import random
import httpx
import hmac
import hashlib
from urllib.parse import parse_qs
from fastapi_cache.decorator import cache

from app.games.honesty.service import HonestyService
from app.users.service import UserService
from app.exceptions import CategoryNotFoundException
from app.config import settings

router_webapp = APIRouter(prefix="", tags=["Frontend"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / 'templates'
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


async def _get_user_context(request: Request, telegram_id: Optional[int]):
    if not telegram_id:
        try:
            sid = request.session.get('telegram_id')
            telegram_id = int(sid) if sid else None
        except Exception:
            telegram_id = None
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
        {"code": "honesty", "title": "Откровенность", "subtitle": "Поговорим откровенно?", "premium": False, "image": "static/media/honesty.png", "in_development": False},
        {"code": "mulabar", "title": "Мулабар", "subtitle": "Выпивай и выполняй задания", "premium": False, "image": "static/media/mulabar.png", "in_development": True},
        {"code": "crocodile", "title": "Крокодил", "subtitle": "Изображай то, что загадано", "premium": False, "image": "static/media/crocodile.png", "in_development": True},
    ]
    ctx = await _get_user_context(request, telegram_id)
    return templates.TemplateResponse('index.html', {"request": request, "games": games, **ctx})


@router_webapp.get('/premium', response_class=HTMLResponse)
async def premium_page(request: Request, telegram_id: Optional[int] = None):
    ctx = await _get_user_context(request, telegram_id)
    return templates.TemplateResponse('premium.html', {"request": request, **ctx, "settings": settings})


@router_webapp.get('/api/premium/status', response_class=JSONResponse)
@cache(expire=10)
async def premium_status(request: Request, telegram_id: Optional[int] = None):
    """Возвращает текущий статус премиума для авторизованного пользователя.

    Использует telegram_id из сессии (после /api/auth) или из параметра.
    """
    if not telegram_id:
        try:
            sid = request.session.get('telegram_id')
            telegram_id = int(sid) if sid else None
        except Exception:
            telegram_id = None
    if not telegram_id:
        raise HTTPException(status_code=401, detail='Not authenticated')

    user, premium = await UserService.get_profile(telegram_id)
    return {
        "telegram_id": telegram_id,
        "premium_active": bool(premium),
        "premium_expire_date": premium.expire_date.isoformat() if premium else None,
    }


@router_webapp.post('/api/premium/payment', response_class=JSONResponse)
async def create_premium_payment(request: Request):
    """Создаёт платёж в YooKassa с embedded-виджетом и возвращает payment_id и confirmation_token.

    Далее фронт инициализирует YooKassaCheckoutWidget внутри WebApp.
    """
    if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
        raise HTTPException(status_code=500, detail="YooKassa не сконфигурирована")

    payload = await request.json()
    duration_days = int(payload.get("duration_days", 365))
    telegram_id = payload.get("telegram_id")
    if not telegram_id:
        # пробуем взять из сессии на всякий случай
        try:
            sid = request.session.get('telegram_id')
            telegram_id = int(sid) if sid else None
        except Exception:
            telegram_id = None
    if not telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id is required")

    amount_value = "2.00"  # TODO: вынести в настройки

    auth = (settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_SECRET_KEY)
    headers = {
        "Idempotence-Key": f"premium-{telegram_id}-{duration_days}",
        "Content-Type": "application/json",
    }

    body = {
        "amount": {"value": amount_value, "currency": "RUB"},
        "confirmation": {"type": "embedded"},
        "capture": True,
        "description": f"Premium {duration_days} days for {telegram_id}",
        "metadata": {"telegram_id": telegram_id, "duration_days": duration_days},
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post("https://api.yookassa.ru/v3/payments", json=body, auth=auth, headers=headers)

    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}
        raise HTTPException(status_code=500, detail={"message": "YooKassa error", "data": data})

    payment = resp.json()
    confirmation = payment.get("confirmation", {})
    if confirmation.get("type") != "embedded":
        raise HTTPException(status_code=500, detail="Unexpected confirmation type from YooKassa")

    return {
        "id": payment.get("id"),
        "status": payment.get("status"),
        "confirmation_token": confirmation.get("confirmation_token"),
    }


@router_webapp.post('/api/yookassa/webhook', response_class=JSONResponse)
async def yookassa_webhook(request: Request):
    """Принимает webhooks от YooKassa и активирует подписку после payment.succeeded.

    В бою нужно валидировать подпись webhook'а.
    """
    event = await request.json()
    event_type = event.get("event")
    obj = event.get("object") or {}

    if event_type == "payment.succeeded":
        metadata = obj.get("metadata") or {}
        telegram_id = metadata.get("telegram_id")
        duration_days = int(metadata.get("duration_days", 365))
        if telegram_id:
            try:
                await UserService.extend_premium(telegram_id=int(telegram_id), duration_days=duration_days)
            except Exception:
                # логика логирования/алертов
                pass

    return {"ok": True}


@router_webapp.get('/honesty', response_class=HTMLResponse)
async def honesty_categories(request: Request, telegram_id: Optional[int] = None):
    ctx = await _get_user_context(request, telegram_id)
    categories = await HonestyService.get_visible_categories()
    return templates.TemplateResponse('honesty_categories.html', {"request": request, "categories": categories, **ctx})


@router_webapp.get('/honesty/play/{category_id}', response_class=HTMLResponse)
async def honesty_play(
    request: Request,
    category_id: int,
    telegram_id: Optional[int] = None,
):
    ctx = await _get_user_context(request, telegram_id)
    try:
        category = await HonestyService.get_category_or_raise(category_id)
    except CategoryNotFoundException:
        raise HTTPException(status_code=404, detail='Категория не найдена')
    if not category.is_visible:
        raise HTTPException(status_code=403, detail='Категория скрыта')
    # Если категория премиум, а подписки нет — не отдаём вопросы, возвращаем 402, фронт покажет попап
    if category.is_premium and not ctx.get('premium'):
        raise HTTPException(status_code=402, detail='Требуется премиум')
    questions = await HonestyService.get_questions(category_id)
    if questions:
        random.shuffle(questions)
    return templates.TemplateResponse('honesty_play.html', {"request": request, "category": category, "questions": questions, **ctx})


# Безопасная авторизация: принимаем initData строкой, валидируем подпись и TTL, кладем telegram_id в сессию
@router_webapp.post('/api/auth', response_class=JSONResponse)
async def webapp_auth(request: Request):
    data = await request.json()
    init_data: str = data.get('initData') or ''
    if not init_data:
        raise HTTPException(status_code=400, detail='initData is required')
    if not settings.BOT_TOKEN:
        raise HTTPException(status_code=500, detail='BOT_TOKEN not configured')

    # Парсим строку initData как query string
    params = parse_qs(init_data, keep_blank_values=True)
    # Извлекаем hash и auth_date
    hash_values = params.get('hash', [])
    auth_values = params.get('auth_date', [])
    if not hash_values or not auth_values:
        raise HTTPException(status_code=400, detail='Invalid initData')
    provided_hash = hash_values[0]
    auth_date_str = auth_values[0]

    items = []
    for k, vs in params.items():
        if k == 'hash':
            continue
        v = vs[0] if isinstance(vs, list) else vs
        items.append(f"{k}={v}")
    items.sort(key=lambda s: s.split('=')[0])
    data_check_string = "\n".join(items)

    secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode('utf-8'), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    if computed_hash != provided_hash:
        raise HTTPException(status_code=401, detail='Invalid signature')

    try:
        auth_ts = int(auth_date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid auth_date')
    import time
    now = int(time.time())
    if now - auth_ts > 3600:
        raise HTTPException(status_code=401, detail='initData expired')

    user_values = params.get('user', [])
    telegram_id = None
    if user_values:
        import json
        try:
            user_obj = json.loads(user_values[0])
            telegram_id = int(user_obj.get('id'))
        except Exception:
            telegram_id = None
    if not telegram_id:
        raise HTTPException(status_code=400, detail='User not found in initData')

    request.session['telegram_id'] = telegram_id

    user, premium = await UserService.get_profile(telegram_id)
    return {"ok": True, "telegram_id": telegram_id, "profile": {
        "first_name": user.first_name,
        "username": user.username,
        "premium_active": bool(premium),
        "premium_expire_date": premium.expire_date.isoformat() if premium else None
    }}
