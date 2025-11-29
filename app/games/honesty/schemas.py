from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from typing import Optional, List


class HonQuestionRead(BaseModel):
    id: int
    category_id: int
    text: str

    model_config = ConfigDict(from_attributes=True)


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
    questions: List[HonQuestionRead] = Field(default_factory=list)

    # Pydantic v2: убираем Deprecated config и сразу включаем чтение из ORM-объектов
    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)
