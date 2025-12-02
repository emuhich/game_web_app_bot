from fastapi import APIRouter, Query
from fastapi_cache.decorator import cache

from app.games.honesty.schemas import (
    HonCategoryRead,
    HonQuestionRead,
)
from app.games.honesty.service import HonestyService

router = APIRouter(prefix='/games/honesty', tags=['Honesty'])


@router.get('/categories', response_model=list[HonCategoryRead])
@cache(expire=60)
async def list_categories(include_hidden: bool = Query(False, description="Показать скрытые категории")):
    categories = await HonestyService.get_visible_categories()
    return [HonCategoryRead.model_validate(c, from_attributes=True) for c in categories]


@router.get('/categories/{category_id}/questions', response_model=list[HonQuestionRead])
async def list_questions(category_id: int):
    questions = await HonestyService.get_questions(category_id)
    return [HonQuestionRead.model_validate(q, from_attributes=True) for q in questions]


@router.get('/questions/{question_id}', response_model=HonQuestionRead)
async def get_question(question_id: int):
    question = await HonestyService.get_question_or_raise(question_id)
