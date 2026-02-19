"""뉴스레터 발신자 CRUD API."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

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
def list_senders():
    """전체 발신자 목록을 반환한다."""
    return get_senders()


@router.post("/senders", response_model=SenderResponse, status_code=201)
def create_sender(body: SenderCreate):
    """새 발신자를 추가한다."""
    try:
        return add_sender(name=body.name, email=body.email)
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다.")
        raise


@router.put("/senders/{sender_id}", response_model=SenderResponse)
def modify_sender(sender_id: str, body: SenderUpdate):
    """발신자 정보를 수정한다."""
    existing = get_sender_by_id(sender_id)
    if not existing:
        raise HTTPException(status_code=404, detail="발신자를 찾을 수 없습니다.")

    try:
        result = update_sender(
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
def remove_sender(sender_id: str):
    """발신자를 삭제한다."""
    if not delete_sender(sender_id):
        raise HTTPException(status_code=404, detail="발신자를 찾을 수 없습니다.")
    return {"status": "deleted"}
