"""뉴스레터 발신자 CRUD API."""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from backend.app.dependencies import get_current_user
from backend.app.services.db import (
    add_sender,
    delete_sender,
    get_sender_by_id,
    get_senders,
    update_sender,
)

router = APIRouter(tags=["senders"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic 모델
# ---------------------------------------------------------------------------

class SenderCreate(BaseModel):
    name: str
    email: EmailStr


class SenderUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class SenderResponse(BaseModel):
    id: str
    name: str
    email: str
    is_active: int
    created_at: str


# ---------------------------------------------------------------------------
# 엔드포인트
# ---------------------------------------------------------------------------

@router.get("/senders", response_model=list[SenderResponse])
def list_senders(user: dict = Depends(get_current_user)):
    """전체 발신자 목록을 반환한다."""
    return get_senders(user["id"])


@router.post("/senders", response_model=SenderResponse, status_code=201)
def create_sender(
    body: SenderCreate,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """새 발신자를 추가한다. 성공 시 백그라운드에서 2일 동기화를 트리거한다."""
    try:
        result = add_sender(user_id=user["id"], name=body.name, email=body.email)
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다.")
        raise

    background_tasks.add_task(_sync_after_sender_add, user["id"])
    return result


@router.put("/senders/{sender_id}", response_model=SenderResponse)
def modify_sender(
    sender_id: str,
    body: SenderUpdate,
    user: dict = Depends(get_current_user),
):
    """발신자 정보를 수정한다."""
    existing = get_sender_by_id(user["id"], sender_id)
    if not existing:
        raise HTTPException(status_code=404, detail="발신자를 찾을 수 없습니다.")

    try:
        result = update_sender(
            user_id=user["id"],
            sender_id=sender_id,
            name=body.name,
            email=body.email,
            is_active=body.is_active,
        )
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다.")
        raise

    return result


@router.delete("/senders/{sender_id}")
def remove_sender(sender_id: str, user: dict = Depends(get_current_user)):
    """발신자를 삭제한다."""
    if not delete_sender(user["id"], sender_id):
        raise HTTPException(status_code=404, detail="발신자를 찾을 수 없습니다.")
    return {"status": "deleted"}


def _sync_after_sender_add(user_id: str) -> None:
    """발신자 등록 후 최근 2일 동기화 + AI 처리를 실행한다."""
    from backend.app.services.gemini import run_ai_processing
    from backend.app.services.gmail import sync_emails
    from backend.app.sync_state import get_user_lock, update_user_sync_status

    lock = get_user_lock(user_id)
    if not lock.acquire(blocking=False):
        logger.info("동기화 이미 진행 중 — 발신자 추가 후 동기화 건너뜀 (user=%s)", user_id)
        return

    try:
        update_user_sync_status(
            user_id, is_syncing=True, phase="gmail_sync",
            message="새 발신자에 대한 뉴스레터를 가져오는 중...",
        )
        sync_emails(user_id, days=2)
        update_user_sync_status(
            user_id, phase="ai_processing", message="AI가 뉴스레터를 분석하고 있습니다..."
        )
        run_ai_processing(user_id)
        update_user_sync_status(user_id, phase="done", message="동기화가 완료되었습니다!")
    except Exception:
        logger.exception("발신자 추가 후 동기화 실패 (user=%s)", user_id)
        update_user_sync_status(user_id, phase="error", message="동기화 중 오류가 발생했습니다.")
    finally:
        update_user_sync_status(user_id, is_syncing=False)
        lock.release()
