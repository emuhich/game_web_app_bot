from fastapi import APIRouter
from app.users.service import UserService
from app.users.schemas import UserProfile, PremiumPurchase, PremiumStatus
from app.exceptions import PremiumDurationInvalidException

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/profile/{telegram_id}', response_model=UserProfile)
async def get_profile(telegram_id: int):
    user, premium = await UserService.get_profile(telegram_id)
    return UserProfile(
        telegram_id=user.telegram_id,
        first_name=user.first_name,
        username=user.username,
        premium_active=bool(premium),
        premium_expire_date=premium.expire_date if premium else None
    )


@router.get('/premium/{telegram_id}', response_model=PremiumStatus)
async def premium_status(telegram_id: int):
    user, premium = await UserService.get_profile(telegram_id)
    return PremiumStatus(active=bool(premium), expire_date=premium.expire_date if premium else None)


@router.post('/premium/{telegram_id}', response_model=PremiumStatus)
async def buy_or_extend_premium(telegram_id: int, payload: PremiumPurchase):
    if payload.duration_days <= 0:
        raise PremiumDurationInvalidException()
    premium = await UserService.extend_premium(telegram_id, payload.duration_days)
    return PremiumStatus(active=True, expire_date=premium.expire_date)


@router.post('/premium/{telegram_id}/auto-renew', response_model=PremiumStatus)
async def toggle_auto_renew(telegram_id: int, enable: bool):
    await UserService.toggle_auto_renew(telegram_id, enable)
    user, premium = await UserService.get_profile(telegram_id)
    return PremiumStatus(active=bool(premium), expire_date=premium.expire_date if premium else None)
