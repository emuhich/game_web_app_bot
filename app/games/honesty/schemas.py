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
    image: Optional[str]
    order: int
    is_visible: bool
    is_premium: bool
    is_adult: bool
    questions: List[HonQuestionRead] = Field(default_factory=list)

    # Pydantic v2: убираем Deprecated config и сразу включаем чтение из ORM-объектов
    model_config = ConfigDict(from_attributes=True)
