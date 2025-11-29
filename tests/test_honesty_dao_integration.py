import pytest
from app.games.honesty.dao import HonCategoryDAO, HonQuestionDAO
from app.db.models.honesty import HonCategory, HonQuestion


@pytest.mark.asyncio
async def test_honesty_category_and_questions():
    # create category via BaseDAO.add
    cat = await HonCategoryDAO.add(
        name="Fun",
        description="Test",
        color="#fff",
        image=None,
        order=1,
        is_visible=True,
        is_premium=False,
        is_adult=False,
    )
    assert isinstance(cat, HonCategory)

    # eager loaded visible
    cats = await HonCategoryDAO.get_visible()
    assert len(cats) >= 1
    assert any(c.id == cat.id for c in cats)

    # add question
    q = await HonQuestionDAO.add_question(category_id=cat.id, text="Question?")
    assert isinstance(q, HonQuestion)

    # list questions
    qs = await HonQuestionDAO.get_by_category(cat.id)
    assert len(qs) == 1
    assert qs[0].text == "Question?"

    # get by id with questions eager
    cat2 = await HonCategoryDAO.get_by_id(cat.id)
    assert isinstance(cat2, HonCategory)
    assert isinstance(cat2.questions, list)

