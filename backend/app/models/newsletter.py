from pydantic import BaseModel


class NewsletterItem(BaseModel):
    date: str
    article_count: int
    selectable: bool = True


class NewsletterListResponse(BaseModel):
    newsletters: list[NewsletterItem]
