from fastapi import APIRouter, Depends

from backend.app.dependencies import get_current_user
from backend.app.models.category import CategoryItem
from backend.app.services.db import get_categories

router = APIRouter()


@router.get("/categories", response_model=list[CategoryItem])
def list_categories(user: dict = Depends(get_current_user)):
    """카테고리별 기사 수를 반환합니다."""
    return get_categories(user["id"])
