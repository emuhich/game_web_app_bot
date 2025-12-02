import logging
from logging.handlers import RotatingFileHandler
from contextlib import asynccontextmanager

import redis.asyncio as redis_async
import uvicorn
from aiogram.types import Update
from fastapi import FastAPI, Request
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from app.admin.views import init_sqladmin
from app.bot.create_bot import bot, dp, stop_bot, start_bot
from app.bot.handlers.user_router import user_router
from app.config import settings
from app.frontend.pages.router import router_webapp
from app.games.honesty.router import router as honesty_router
from app.games.router import router as games_router
from app.users.router import router as users_router


def setup_logging() -> None:
    """Базовая конфигурация логирования для приложения.

    - Логируем в stdout (для Docker) и в файл с ротацией.
    - Настройки управляются через `settings` (уровень, формат, директория).
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    log_format = settings.LOG_FORMAT

    # Глобальный логгер
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Удаляем все старые хендлеры, если они уже были настроены
    for h in list(logger.handlers):
        logger.removeHandler(h)

    formatter = logging.Formatter(log_format)

    # Логирование в stdout — важно для Docker
    if settings.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Логирование в файл с ротацией
    if settings.LOG_TO_FILE:
        try:
            log_dir = settings.LOG_DIR
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_dir / "app.log",
                maxBytes=5 * 1024 * 1024,  # 5 MB
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Если по каким-то причинам нельзя писать в файл, не падаем, а просто логируем в консоль
            logging.basicConfig(level=log_level, format=log_format)
            logging.getLogger(__name__).warning("Не удалось настроить файловый логгер: %s", e)


# Настраиваем логирование до создания приложения
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting bot & cache setup...")
    # Подключаем роутеры бота
    dp.include_router(user_router)
    # Стартуем бота
    await start_bot()
    webhook_url = settings.get_webhook_url()
    await bot.set_webhook(url=webhook_url,
                          allowed_updates=dp.resolve_used_update_types(),
                          drop_pending_updates=True)
    logger.info("Webhook set to %s", webhook_url)
    # Инициализация Redis-кеша FastAPI (замена устаревшего @on_event startup)
    redis = await redis_async.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    logger.info("FastAPI cache initialized")
    # Переходим к работе приложения
    yield
    # Завершение: удаляем вебхук и останавливаем бота
    logger.info("Shutting down bot...")
    await bot.delete_webhook()
    await stop_bot()
    logger.info("Bot shutdown complete")


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.ADMIN_SECRET)


STATIC_DIR = settings.STATIC_DIR
MEDIA_DIR = settings.MEDIA_DIR
logger.info("[PATHS] STATIC_DIR=%s | MEDIA_DIR=%s", STATIC_DIR.resolve(), MEDIA_DIR.resolve())

if STATIC_DIR.exists():
    app.mount('/static', StaticFiles(directory=str(STATIC_DIR), follow_symlink=True), name='static')
    logger.info("[STATIC] mounted at /static → %s", STATIC_DIR)
else:
    logger.warning("[STATIC] Directory not found, skip mount: %s", STATIC_DIR)

if MEDIA_DIR.exists():
    app.mount('/media', StaticFiles(directory=str(MEDIA_DIR), follow_symlink=True), name='media')
    logger.info("[MEDIA] mounted at /media → %s", MEDIA_DIR)
else:
    logger.warning("[MEDIA] Directory not found: %s", MEDIA_DIR)

init_sqladmin(app)

app.include_router(users_router)
app.include_router(games_router)
app.include_router(honesty_router)
app.include_router(router_webapp)


@app.post("/webhook")
async def webhook(request: Request) -> None:
    logger.info("Received webhook request")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    logger.info("Update processed")


@app.get('/health')
async def health() -> dict:
    """Простой healthcheck: возвращает 200 и минимум информации."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", reload=True)
