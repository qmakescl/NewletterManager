from fastapi import APIRouter, Depends

from backend.app.dependencies import get_current_user
from backend.app.models.newsletter import NewsletterListResponse
from backend.app.services.db import get_newsletters

router = APIRouter(tags=["newsletters"])


@router.get("/newsletters", response_model=NewsletterListResponse)
def list_newsletters(user: dict = Depends(get_current_user)):
    """뉴스레터 날짜 목록을 반환한다 (캘린더 UI용)."""
    newsletters = get_newsletters(user["id"])
    return NewsletterListResponse(newsletters=newsletters)
