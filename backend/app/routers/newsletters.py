from fastapi import APIRouter

from backend.app.models.newsletter import NewsletterListResponse
from backend.app.services.db import get_newsletters

router = APIRouter(tags=["newsletters"])


@router.get("/newsletters", response_model=NewsletterListResponse)
def list_newsletters():
    """뉴스레터 날짜 목록을 반환한다 (캘린더 UI용)."""
    newsletters = get_newsletters()
    return NewsletterListResponse(newsletters=newsletters)
