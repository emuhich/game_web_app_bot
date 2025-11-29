import pytest
from app.users.service import UserService
from app.users.dao import UserDAO


@pytest.mark.asyncio
async def test_get_profile_not_found(monkeypatch):
    async def fake_get_by_telegram(telegram_id: int):
        return None
    monkeypatch.setattr(UserDAO, "get_by_telegram", fake_get_by_telegram)

    with pytest.raises(Exception) as exc:
        await UserService.get_profile(telegram_id=1)
    assert exc.value.__class__.__name__ == "UserNotFoundException"


@pytest.mark.asyncio
async def test_extend_premium_invalid_duration():
    with pytest.raises(Exception) as exc:
        await UserService.extend_premium(telegram_id=1, duration_days=0)
    assert exc.value.__class__.__name__ == "PremiumDurationInvalidException"

