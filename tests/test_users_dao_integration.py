import pytest
from app.users.dao import UserDAO
from app.db.models.users import User, Premium


@pytest.mark.asyncio
async def test_user_crud_and_premium_flow():
    # create
    u = await UserDAO.get_or_create(telegram_id=123, first_name="Ivan", username="ivan")
    assert isinstance(u, User)
    assert u.telegram_id == 123

    # read
    u2 = await UserDAO.get_by_telegram(123)
    assert u2 is not None
    assert u2.first_name == "Ivan"

    # update username
    ok = await UserDAO.update_username(123, "ivan_updated")
    assert ok
    u3 = await UserDAO.get_by_telegram(123)
    assert u3.username == "ivan_updated"

    # premium extend
    p = await UserDAO.extend_premium(telegram_id=123, duration_days=7)
    assert isinstance(p, Premium)

    # toggle auto renew
    ok2 = await UserDAO.toggle_auto_renew(123, True)
    assert ok2

    # list active
    active = await UserDAO.list_active()
    assert any(x.telegram_id == 123 for x in active)

    # deactivate
    ok3 = await UserDAO.deactivate(123)
    assert ok3
    active2 = await UserDAO.list_active()
    assert not any(x.telegram_id == 123 for x in active2)

