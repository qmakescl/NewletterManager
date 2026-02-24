from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.dependencies import get_current_user
from backend.app.models.article import ArticleDetailResponse, ArticleListResponse
from backend.app.services.db import get_article_by_id, get_articles

router = APIRouter(tags=["articles"])


@router.get("/articles", response_model=ArticleListResponse)
def list_articles(
    user: dict = Depends(get_current_user),
    dates: Optional[str] = Query(
        None, description="콤마 구분 날짜 목록 (예: 2026-02-18,2026-02-17)"
    ),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(24, ge=1, le=100, description="페이지 크기"),
):
    date_list = [d.strip() for d in dates.split(",")] if dates else None
    result = get_articles(user["id"], dates=date_list, category=category, page=page, size=size)
    return ArticleListResponse(
        total=result["total"],
        selected_dates=date_list or [],
        items=result["items"],
    )


@router.get("/articles/{article_id}", response_model=ArticleDetailResponse)
def get_article(article_id: str, user: dict = Depends(get_current_user)):
    article = get_article_by_id(user["id"], article_id)
    if not article:
        raise HTTPException(status_code=404, detail="기사를 찾을 수 없습니다.")
    return article
