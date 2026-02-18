from fastapi import APIRouter, Query

from backend.app.models.article import ArticleListResponse
from backend.app.services.db import get_article_by_id
from backend.app.services.vector import search_similar

router = APIRouter(tags=["search"])


@router.get("/search", response_model=ArticleListResponse)
def semantic_search(
    q: str = Query(..., min_length=2, description="검색 질의"),
):
    """시맨틱 검색: ChromaDB 유사도 기반으로 관련 기사를 반환한다."""
    similar = search_similar(query=q, top_k=10)

    articles = []
    for item in similar:
        article = get_article_by_id(item["id"])
        if article:
            articles.append(article)

    return ArticleListResponse(total=len(articles), items=articles)
