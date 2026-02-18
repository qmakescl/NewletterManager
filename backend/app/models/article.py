from datetime import datetime

from pydantic import BaseModel


class ArticleBase(BaseModel):
    id: str
    title: str
    summary_en: str | None = None
    summary_ko: str | None = None
    url: str | None = None
    category: str = "Other"
    tags: list[str] = []
    importance: int = 0
    published_at: str | None = None
    email_id: str | None = None
    newsletter_id: str | None = None
    ai_processed: int = 0


class ArticleListResponse(BaseModel):
    total: int
    selected_dates: list[str] = []
    items: list[ArticleBase]


class ArticleDetailResponse(ArticleBase):
    pass
