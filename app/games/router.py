from fastapi import APIRouter

GAMES = [
    {"slug": "honesty", "name": "Откровенность", "description": "Игра с откровенными вопросами", "is_active": True,
     "image": "static/media/honesty.png"}
]

router = APIRouter(prefix="/games", tags=["Games"])


@router.get("/", response_model=list[dict])
async def list_games():
    return GAMES
