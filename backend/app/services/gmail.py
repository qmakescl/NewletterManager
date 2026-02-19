"""Gmail API 연동 서비스.

Google OAuth 2.0 인증, TLDR AI 뉴스레터 수집, 동기화 파이프라인을 제공한다.
"""

import base64
import logging
import os
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from backend.app.config import settings
from backend.app.services.db import get_active_sender_emails, insert_newsletter, newsletter_exists
from backend.app.services.parser import parse_tldr_email

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
TOKEN_PATH = str(_BACKEND_DIR / "token.json")


def get_gmail_service():
    """Gmail API 서비스 인스턴스를 반환한다.

    최초 실행 시 브라우저 기반 OAuth 인증을 수행하고, 이후에는 token.json을 사용한다.
    """
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = str(settings.gmail_credentials_path)
            if not os.path.isabs(credentials_path):
                credentials_path = str(_BACKEND_DIR / credentials_path)

            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"OAuth credentials 파일을 찾을 수 없습니다: {credentials_path}\n"
                    "Google Cloud Console에서 OAuth 2.0 클라이언트 자격증명을 발급받고 "
                    "credentials.json으로 저장해주세요."
                )

            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        logger.info("OAuth 토큰 저장 완료: %s", TOKEN_PATH)

    return build("gmail", "v1", credentials=creds)


def fetch_tldr_emails(days: int = 30) -> list[dict[str, Any]]:
    """최근 N일간의 TLDR AI 뉴스레터 이메일을 가져온다."""
    active_emails = get_active_sender_emails()
    if not active_emails:
        logger.warning("활성 발신자가 없습니다. Gmail 검색을 건너뜁니다.")
        return []

    service = get_gmail_service()
    after_date = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    sender_parts = " OR ".join(f"from:{s}" for s in active_emails)
    query = f"({sender_parts}) after:{after_date}"

    logger.info("Gmail 검색: %s", query)

    messages: list[dict] = []
    page_token = None

    while True:
        result = (
            service.users()
            .messages()
            .list(userId="me", q=query, pageToken=page_token)
            .execute()
        )

        if "messages" in result:
            messages.extend(result["messages"])

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    logger.info("총 %d개 메시지 발견", len(messages))

    full_messages = []
    for msg_ref in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_ref["id"], format="full")
            .execute()
        )
        full_messages.append(msg)

    return full_messages


def get_message_id(message: dict[str, Any]) -> str:
    """Gmail 메시지에서 Message-ID 헤더를 추출한다."""
    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        if header["name"].lower() == "message-id":
            return header["value"]
    return message["id"]


def get_message_date(message: dict[str, Any]) -> str:
    """Gmail 메시지에서 날짜를 추출하여 YYYY-MM-DD 형식으로 반환한다."""
    headers = message.get("payload", {}).get("headers", [])
    for header in headers:
        if header["name"].lower() == "date":
            try:
                dt = parsedate_to_datetime(header["value"])
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass

    # fallback: Gmail 내부 타임스탬프 사용
    internal_date = message.get("internalDate")
    if internal_date:
        dt = datetime.fromtimestamp(int(internal_date) / 1000)
        return dt.strftime("%Y-%m-%d")

    return datetime.now().strftime("%Y-%m-%d")


def get_message_body(message: dict[str, Any]) -> tuple[str, str]:
    """Gmail 메시지에서 HTML과 plain text 본문을 추출한다.

    Returns:
        (html_body, plain_text_body) 튜플
    """
    html_body = ""
    text_body = ""

    payload = message.get("payload", {})
    _extract_parts(payload, html_body_parts := [], text_body_parts := [])

    if html_body_parts:
        html_body = "\n".join(html_body_parts)
    if text_body_parts:
        text_body = "\n".join(text_body_parts)

    return html_body, text_body


def _extract_parts(
    part: dict[str, Any],
    html_parts: list[str],
    text_parts: list[str],
) -> None:
    """MIME 파트 트리를 재귀적으로 순회하여 본문을 추출한다."""
    mime_type = part.get("mimeType", "")

    if "parts" in part:
        for sub_part in part["parts"]:
            _extract_parts(sub_part, html_parts, text_parts)
    elif mime_type == "text/html":
        data = part.get("body", {}).get("data", "")
        if data:
            decoded = base64.urlsafe_b64decode(data).decode("utf-8")
            html_parts.append(decoded)
    elif mime_type == "text/plain":
        data = part.get("body", {}).get("data", "")
        if data:
            decoded = base64.urlsafe_b64decode(data).decode("utf-8")
            text_parts.append(decoded)


# ---------------------------------------------------------------------------
# 동기화 파이프라인
# ---------------------------------------------------------------------------

def sync_emails(days: int = 30) -> dict[str, int]:
    """Gmail 동기화 파이프라인: 수집 → 중복 체크 → 파싱 → DB 저장.

    Returns:
        처리 결과 요약 딕셔너리
    """
    logger.info("Gmail 동기화 시작 (최근 %d일)", days)

    messages = fetch_tldr_emails(days=days)
    new_count = 0
    skipped_count = 0
    error_count = 0

    for msg in messages:
        email_id = get_message_id(msg)

        if newsletter_exists(email_id):
            skipped_count += 1
            continue

        try:
            published_date = get_message_date(msg)
            html_body, text_body = get_message_body(msg)
            parsed_articles = parse_tldr_email(html_body, text_body)

            if parsed_articles:
                insert_newsletter(
                    email_id=email_id,
                    published_date=published_date,
                    articles=[
                        {
                            "title": a.title,
                            "summary_en": a.summary_en,
                            "url": a.url,
                        }
                        for a in parsed_articles
                    ],
                )
                new_count += 1
                logger.info(
                    "뉴스레터 저장: %s (%d개 기사)", published_date, len(parsed_articles)
                )
            else:
                logger.warning("파싱 결과 없음: email_id=%s", email_id)
                error_count += 1
        except Exception:
            logger.exception("뉴스레터 처리 실패: email_id=%s", email_id)
            error_count += 1

    result = {
        "total_fetched": len(messages),
        "new_newsletters": new_count,
        "skipped_duplicates": skipped_count,
        "errors": error_count,
    }
    logger.info("Gmail 동기화 완료: %s", result)
    return result
