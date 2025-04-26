from .base import BaseModel


class ThemeModel(BaseModel):
    id: int
    name: str
    description: str
    gpt: str
