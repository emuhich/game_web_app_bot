from pydantic import BaseModel
from typing import Optional
from datetime import date


class UserProfile(BaseModel):
    telegram_id: int
    first_name: str
    username: Optional[str]
    premium_active: bool
    premium_expire_date: Optional[date]


class PremiumPurchase(BaseModel):
    duration_days: int


class PremiumStatus(BaseModel):
    active: bool
    expire_date: Optional[date]
