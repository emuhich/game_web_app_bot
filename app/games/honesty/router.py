from fastapi import APIRouter, Query
from app.games.honesty.service import HonestyService
from app.games.honesty.schemas import (
    HonCategoryRead,
    HonQuestionRead,
    HonCategoryCreate,
    HonQuestionCreate,
)

router = APIRouter(prefix='/games/honesty', tags=['Honesty'])


@router.get('/categories', response_model=list[HonCategoryRead])
async def list_categories(include_hidden: bool = Query(False, description="Показать скрытые категории")):
    categories = await HonestyService.get_visible_categories()
    return [HonCategoryRead.model_validate(c) for c in categories]


@router.get('/categories/{category_id}/questions', response_model=list[HonQuestionRead])
async def list_questions(category_id: int):
    questions = await HonestyService.get_questions(category_id)
    return [HonQuestionRead.model_validate(q) for q in questions]


@router.post('/categories', response_model=HonCategoryRead)
async def create_category(payload: HonCategoryCreate):
    category = await HonestyService.create_category(**payload.model_dump())
    return HonCategoryRead.model_validate(category)


@router.post('/questions', response_model=HonQuestionRead)
async def create_question(payload: HonQuestionCreate):
    question = await HonestyService.create_question(**payload.model_dump())
    return HonQuestionRead.model_validate(question)


@router.get('/questions/{question_id}', response_model=HonQuestionRead)
async def get_question(question_id: int):
    question = await HonestyService.get_question_or_raise(question_id)
    return HonQuestionRead.model_validate(question)
