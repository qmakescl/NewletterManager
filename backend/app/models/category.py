from pydantic import BaseModel


class CategoryItem(BaseModel):
    name: str
    count: int
