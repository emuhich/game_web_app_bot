# Telegram Mini App — платформа игр

Telegram Mini App с мини-играми и премиум-подпиской: FastAPI-бэкенд, бот на aiogram 3 (webhook в том же приложении), фронтенд Mini App на Jinja2 + JS, приём платежей через ЮKassa.

## Возможности

- **Mini App внутри Telegram** — авторизация через `initData`, haptic feedback, нативные попапы
- **Игры по категориям** — вопросы и категории управляются из админки
- **Премиум-доступ** — оплата через ЮKassa
- **Реферальная система**
- **Админ-панель** на SQLAdmin: пользователи, категории, вопросы, дашборд

## Стек

| Слой | Технологии |
|---|---|
| API | FastAPI, Pydantic v2, pydantic-settings |
| Бот | aiogram 3 (webhook через общий FastAPI-инстанс) |
| БД | PostgreSQL, SQLAlchemy 2 (async), Alembic |
| Кэш | Redis + fastapi-cache2 |
| Админка | SQLAdmin |
| Платежи | ЮKassa |
| Тесты | pytest, pytest-asyncio |
| Инфраструктура | Docker, docker-compose, gunicorn/uvicorn |

## Архитектура

Слоистая структура: `router → service → DAO → модели`.

```
app/
├── main.py            # точка входа: FastAPI + webhook бота + логирование
├── config.py          # настройки через pydantic-settings (.env)
├── bot/               # aiogram: хендлеры, клавиатуры
├── users/             # роутер / сервис / DAO пользователей
├── games/
│   └── honesty/       # игра: роутер / сервис / DAO / схемы
├── dao/base.py        # базовый generic-DAO (SQLAlchemy 2)
├── db/                # engine, session, модели
├── admin/             # SQLAdmin views
├── frontend/          # страницы Mini App: Jinja2-шаблоны + static JS/CSS
└── migrations/        # Alembic
tests/                 # юнит- и интеграционные тесты
```

## Тесты

- Юнит-тесты сервисов с моками DAO
- Интеграционные тесты DAO на in-memory SQLite (async), схема создаётся из моделей
- Smoke-тесты роутеров

```bash
pip install -r requirements.txt pytest pytest-asyncio
pytest -q
```

## Запуск

```bash
cp .env.example .env   # заполнить BOT_TOKEN, BASE_SITE, доступы к БД/Redis
docker-compose up --build
```

Миграции применяются через Alembic:

```bash
alembic upgrade head
```
