"""Google OAuth 인증 라우터."""

import json
import logging
from datetime import datetime, timedelta, timezone

import httpx
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Response
from jose import jwt

from backend.app.config import settings
from backend.app.dependencies import ALGORITHM, get_current_user
from backend.app.services.db import upsert_user

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

SCOPES = "openid email profile https://www.googleapis.com/auth/gmail.readonly"


def _get_fernet() -> Fernet:
    return Fernet(settings.token_encryption_key.encode())


def _create_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


@router.get("/login")
def login():
    """Google OAuth URL을 반환한다."""
    redirect_uri = f"{settings.frontend_url.rstrip('/')}/auth/callback"
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = GOOGLE_AUTH_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
    return {"auth_url": auth_url}


@router.get("/callback")
async def callback(code: str, response: Response):
    """Google OAuth 콜백: 코드 교환 → 사용자 생성/업데이트 → JWT 쿠키 발급."""
    redirect_uri = f"{settings.frontend_url.rstrip('/')}/auth/callback"

    # 1) 코드 → 토큰 교환
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    if token_resp.status_code != 200:
        logger.error("Token exchange failed: %s", token_resp.text)
        raise HTTPException(status_code=400, detail="Google 인증에 실패했습니다.")

    token_data = token_resp.json()
    access_token = token_data["access_token"]

    # 2) 사용자 정보 조회
    async with httpx.AsyncClient() as client:
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if userinfo_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="사용자 정보 조회에 실패했습니다.")

    userinfo = userinfo_resp.json()

    # 3) Gmail 토큰 암호화 저장
    fernet = _get_fernet()
    gmail_token_json = json.dumps({
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "token_uri": GOOGLE_TOKEN_URL,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "scopes": SCOPES.split(),
    })
    encrypted_token = fernet.encrypt(gmail_token_json.encode()).decode()

    expiry = None
    if "expires_in" in token_data:
        expiry = (
            datetime.now(timezone.utc) + timedelta(seconds=token_data["expires_in"])
        ).isoformat()

    # 4) 사용자 upsert
    user = upsert_user(
        google_id=userinfo["sub"],
        email=userinfo["email"],
        name=userinfo.get("name", ""),
        picture_url=userinfo.get("picture"),
        gmail_token_encrypted=encrypted_token,
        gmail_token_expiry=expiry,
    )

    # 5) JWT 쿠키 발급
    jwt_token = _create_jwt(user["id"])
    response.set_cookie(
        key="session",
        value=jwt_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
        secure=False,  # 개발 환경; 프로덕션에서 True로 변경
    )

    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "picture_url": user.get("picture_url"),
        },
        "token": jwt_token,
    }


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    """현재 로그인한 사용자 정보를 반환한다."""
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "picture_url": user.get("picture_url"),
    }


@router.post("/logout")
def logout(response: Response):
    """세션 쿠키를 삭제한다."""
    response.delete_cookie(key="session")
    return {"status": "logged_out"}
