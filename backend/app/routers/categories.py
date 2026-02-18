from fastapi import APIRouter

from backend.app.models.category import CategoryItem
from backend.app.services.db import get_categories

router = APIRouter()


@router.get("/categories", response_model=list[CategoryItem])
def list_categories():
    """카테고리별 기사 수를 반환합니다."""
    return get_categories()
