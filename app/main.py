import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
import redis.asyncio as redis_async
from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from app.admin.views import init_sqladmin
from app.bot.create_bot import bot, dp, stop_bot, start_bot
from app.bot.handlers.admin_router import admin_router as admin_router_bot
from app.bot.handlers.user_router import user_router
from app.config import settings
from app.games.honesty.router import router as honesty_router
from app.games.router import router as games_router
from app.users.router import router as users_router
from app.frontend.pages.router import router as router_pages

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting bot & cache setup...")
    # Подключаем роутеры бота
    dp.include_router(user_router)
    dp.include_router(admin_router_bot)
    # Стартуем бота
    await start_bot()
    webhook_url = settings.get_webhook_url()
    await bot.set_webhook(url=webhook_url,
                          allowed_updates=dp.resolve_used_update_types(),
                          drop_pending_updates=True)
    logging.info(f"Webhook set to {webhook_url}")
    # Инициализация Redis-кеша FastAPI (замена устаревшего @on_event startup)
    redis = await redis_async.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    logging.info("FastAPI cache initialized")
    # Переходим к работе приложения
    yield
    # Завершение: удаляем вебхук и останавливаем бота
    logging.info("Shutting down bot...")
    await bot.delete_webhook()
    await stop_bot()
    logging.info("Bot shutdown complete")


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.ADMIN_SECRET)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / 'frontend' / 'static'
MEDIA_DIR = PROJECT_ROOT / 'media'

if STATIC_DIR.exists():
    app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')
else:
    logging.warning(f"Static directory not found: {STATIC_DIR}")

if MEDIA_DIR.exists():
    app.mount('/media', StaticFiles(directory=str(MEDIA_DIR)), name='media')
else:
    logging.warning(f"Media directory not found: {MEDIA_DIR}")

init_sqladmin(app)

app.include_router(users_router)
app.include_router(games_router)
app.include_router(honesty_router)
app.include_router(router_pages)


@app.post("/webhook")
async def webhook(request: Request) -> None:
    logging.info("Received webhook request")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    logging.info("Update processed")


if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)
