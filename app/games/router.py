from fastapi import APIRouter
from fastapi_cache.decorator import cache

GAMES = [
    {
        "slug": "honesty",
        "name": "Откровенность",
        "description": "Игра с откровенными вопросами",
        "is_active": True,
        "image": "static/media/honesty.png",
        "in_development": False,
    },
    {
        "slug": "mulabar",
        "name": "Мулабар",
        "description": "Игра, в которой нужно выпивать и выполнять задания",
        "is_active": True,
        "image": "static/media/mulabar.png",
        "in_development": True,
    },
    {
        "slug": "crocodile",
        "name": "Крокодил",
        "description": "Игра, в которой нужно изображать то, что тебе скажут",
        "is_active": True,
        "image": "static/media/crocodile.png",
        "in_development": True,
    },
]

router = APIRouter(prefix="/games", tags=["Games"])


@router.get("/", response_model=list[dict])
@cache(expire=60)
async def list_games():
    return GAMES
