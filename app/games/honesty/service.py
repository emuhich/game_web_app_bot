from typing import Optional
from app.games.honesty.dao import HonCategoryDAO, HonQuestionDAO
from app.exceptions import CategoryNotFoundException, QuestionNotFoundException


class HonestyService:
    @staticmethod
    async def get_visible_categories():
        return await HonCategoryDAO.get_visible()

    @staticmethod
    async def get_category_or_raise(category_id: int):
        category = await HonCategoryDAO.get_by_id(category_id)
        if not category:
            raise CategoryNotFoundException()
        return category

    @staticmethod
    async def get_questions(category_id: int):
        # убеждаемся что категория существует
        await HonestyService.get_category_or_raise(category_id)
        return await HonQuestionDAO.get_by_category(category_id)

    @staticmethod
    async def get_question_or_raise(question_id: int):
        question = await HonQuestionDAO.get_one_or_none(id=question_id)
        if not question:
            raise QuestionNotFoundException()
        return question
