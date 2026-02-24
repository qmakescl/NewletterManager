"""JWT 인증 의존성."""

import logging

from fastapi import Cookie, HTTPException, Request
from jose import JWTError, jwt

from backend.app.config import settings
from backend.app.services.db import get_user_by_id

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"


def get_current_user(request: Request, session: str | None = Cookie(default=None)) -> dict:
    """JWT 쿠키 또는 Authorization 헤더에서 사용자를 추출한다.

    Returns:
        사용자 정보 딕셔너리 (id, email, name, picture_url 등)
    """
    token = session

    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")

    return user
