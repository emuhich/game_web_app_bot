from pydantic import BaseModel
from typing import Optional, List


class HonQuestionRead(BaseModel):
    id: int
    category_id: int
    text: str


class HonCategoryRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: Optional[str]
    image: Optional[str]
    order: int
    is_visible: bool
    is_premium: bool
    is_adult: bool
    questions: List[HonQuestionRead] = []


class HonCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    image: Optional[str] = None
    order: int = 0
    is_visible: bool = True
    is_premium: bool = False
    is_adult: bool = False


class HonQuestionCreate(BaseModel):
    category_id: int
    text: str
