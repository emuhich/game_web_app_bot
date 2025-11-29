import pytest
from app.games.honesty.service import HonestyService
from app.games.honesty.dao import HonCategoryDAO, HonQuestionDAO


@pytest.mark.asyncio
async def test_list_visible_categories(monkeypatch):
    class Dummy:
        id = 1
        name = "Cat"
        description = None
        color = None
        image = None
        order = 0
        is_visible = True
        is_premium = False
        is_adult = False
        questions = []

    async def fake_get_visible():
        return [Dummy()]

    monkeypatch.setattr(HonCategoryDAO, "get_visible", fake_get_visible)
    cats = await HonestyService.get_visible_categories()
    assert len(cats) == 1
    assert cats[0].name == "Cat"


@pytest.mark.asyncio
async def test_get_questions_checks_category(monkeypatch):
    async def fake_get_by_id(category_id: int):
        return object()
    async def fake_get_questions(category_id: int):
        return []
    monkeypatch.setattr(HonCategoryDAO, "get_by_id", fake_get_by_id)
    monkeypatch.setattr(HonQuestionDAO, "get_by_category", fake_get_questions)
    res = await HonestyService.get_questions(1)
    assert res == []

