"""Gemini AI 처리 서비스.

기사 배치 분류/요약, 무료 한도 보호, RAG 파이프라인을 제공한다.
"""

import json
import logging
import time
from datetime import date
from typing import Any

from google import genai

from backend.app.config import settings
from backend.app.services.db import (
    get_daily_api_count,
    get_unprocessed_articles,
    increment_api_count,
    update_article_ai_data,
)

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


CATEGORIES = ["LLM", "Vision", "Agent", "Tools", "Policy", "Research", "Hardware", "Other"]

_BATCH_PROMPT = """\
다음 AI 뉴스 기사 {count}개를 분석해주세요.

각 기사에 대해 JSON 배열로 응답해주세요. 각 항목은 다음 필드를 포함해야 합니다:
- "index": 기사 번호 (0부터 시작)
- "category": 반드시 다음 중 하나: {categories}
- "summary_ko": 한국어 요약 (2-3문장, 핵심 내용 중심)
- "importance": 1-5 정수 (산업 영향력 기준, 5가 가장 높음)
- "tags": 키워드 태그 배열 (최대 5개, 모델명/기업명/기술용어)

기사 목록:
{articles}

JSON 배열만 응답해주세요. 마크다운 코드블록이나 다른 텍스트 없이 순수 JSON만 출력하세요.\
"""

_RAG_PROMPT = """\
당신은 AI 뉴스 전문가입니다. 아래 참고 기사들을 바탕으로 사용자의 질문에 한국어로 답변해주세요.

참고 기사:
{context}

사용자 질문: {query}

답변 규칙:
1. 참고 기사의 내용만을 바탕으로 답변하세요.
2. 관련 기사가 없으면 솔직하게 모른다고 말해주세요.
3. 반드시 다음 JSON 형식으로만 응답하세요:
{{"answer": "한국어 답변 내용", "source_ids": ["기사id1", "기사id2"]}}\
"""


# ---------------------------------------------------------------------------
# 핵심 API 호출 (지수 백오프)
# ---------------------------------------------------------------------------

def _call_with_retry(prompt: str, max_retries: int = 3) -> str:
    """Gemini API 호출. 429 에러 시 지수 백오프(1s→2s→4s)로 재시도."""
    client = _get_client()
    delay = 1.0

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if ("429" in error_str or "RESOURCE_EXHAUSTED" in error_str) and attempt < max_retries:
                logger.warning(
                    "Rate limit 감지 (시도 %d/%d), %.1f초 대기", attempt + 1, max_retries, delay
                )
                time.sleep(delay)
                delay *= 2
            else:
                raise

    raise RuntimeError("Gemini API 최대 재시도 횟수 초과")


def _parse_json_response(text: str) -> list[dict[str, Any]]:
    """Gemini 응답에서 JSON을 추출하여 파싱한다."""
    text = text.strip()

    # 마크다운 코드블록 제거
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # JSON 배열 부분만 추출 시도
        import re
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise


# ---------------------------------------------------------------------------
# 배치 AI 처리
# ---------------------------------------------------------------------------

def _check_daily_limit() -> bool:
    """일일 API 호출 한도를 확인한다. 초과 시 False를 반환한다."""
    today = date.today()
    count = get_daily_api_count(today)
    if count >= settings.daily_api_call_limit:
        logger.warning(
            "일일 API 호출 한도 도달: %d/%d", count, settings.daily_api_call_limit
        )
        return False
    if count >= settings.daily_api_call_limit * 0.9:
        logger.warning(
            "일일 API 호출 한도 90%% 도달: %d/%d", count, settings.daily_api_call_limit
        )
    return True


def process_articles_batch(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """기사 배치(최대 5개)를 Gemini로 처리하여 분류/요약 결과를 반환한다."""
    if not articles:
        return []

    if not _check_daily_limit():
        return []

    articles_text = ""
    for i, art in enumerate(articles):
        articles_text += f"\n[{i}] 제목: {art['title']}\n"
        if art.get("summary_en"):
            articles_text += f"    영문 요약: {art['summary_en']}\n"
        if art.get("url"):
            articles_text += f"    URL: {art['url']}\n"

    prompt = _BATCH_PROMPT.format(
        count=len(articles),
        categories=", ".join(CATEGORIES),
        articles=articles_text,
    )

    try:
        response_text = _call_with_retry(prompt)
        increment_api_count()
        logger.debug("API 호출 완료. 오늘 총 %d회", get_daily_api_count())

        results = _parse_json_response(response_text)
        return results
    except Exception:
        logger.exception("배치 처리 실패 (기사 수: %d)", len(articles))
        return []


def run_ai_processing() -> dict[str, int]:
    """미처리 기사 전체를 5개 배치로 AI 처리한다.

    Returns:
        처리 결과 요약 딕셔너리
    """
    from backend.app.services.vector import add_articles_to_vector_db

    processed_count = 0
    failed_count = 0

    logger.info("AI 처리 시작")

    while True:
        if not _check_daily_limit():
            logger.warning("일일 한도 초과로 AI 처리 중단")
            break

        batch = get_unprocessed_articles(batch_size=5)
        if not batch:
            logger.info("미처리 기사 없음. AI 처리 완료")
            break

        results = process_articles_batch(batch)
        if not results:
            failed_count += len(batch)
            break

        vector_batch = []
        for article, result in zip(batch, results):
            try:
                summary_ko = result.get("summary_ko", "")
                category = result.get("category", "Other")
                importance = int(result.get("importance", 0))
                tags = result.get("tags", [])

                # DB 업데이트
                update_article_ai_data(
                    article_id=article["id"],
                    summary_ko=summary_ko,
                    category=category,
                    importance=importance,
                    tags=tags,
                )

                vector_batch.append({
                    "article_id": article["id"],
                    "title": article["title"],
                    "summary_en": article.get("summary_en", ""),
                    "summary_ko": summary_ko,
                    "category": category,
                    "tags": tags,
                })
                processed_count += 1
            except Exception:
                logger.exception("기사 처리 실패: id=%s", article.get("id"))
                failed_count += 1

        # 배치 전체를 한 번의 임베딩 API 호출로 벡터 DB 저장
        if vector_batch:
            add_articles_to_vector_db(vector_batch)

    result = {"processed": processed_count, "failed": failed_count}
    logger.info("AI 처리 완료: %s", result)
    return result


# ---------------------------------------------------------------------------
# RAG 파이프라인
# ---------------------------------------------------------------------------

def rag_query(user_message: str) -> dict[str, Any]:
    """RAG 파이프라인: 질의 → 벡터 검색 → context 구성 → Gemini 답변 생성."""
    from backend.app.services.db import get_article_by_id
    from backend.app.services.vector import search_similar

    # 1단계: 유사 기사 검색
    similar = search_similar(query=user_message, top_k=10)

    # 2단계: context 구성
    context_parts: list[str] = []
    source_ids: list[str] = []

    for item in similar:
        article = get_article_by_id(item["id"])
        if not article:
            continue
        source_ids.append(article["id"])
        context_parts.append(
            f"[ID: {article['id']}] {article['title']}\n"
            f"  영문: {article.get('summary_en', '')}\n"
            f"  한국어: {article.get('summary_ko', '')}\n"
            f"  카테고리: {article.get('category', '')}"
        )

    context = "\n\n".join(context_parts) if context_parts else "관련 기사를 찾을 수 없습니다."

    if not _check_daily_limit():
        return {
            "answer": "일일 API 호출 한도에 도달했습니다. 내일 다시 시도해주세요.",
            "sources": [],
        }

    # 3단계: Gemini 답변 생성
    prompt = _RAG_PROMPT.format(context=context, query=user_message)
    try:
        response_text = _call_with_retry(prompt)
        increment_api_count()
    except Exception:
        logger.exception("RAG 쿼리 실패")
        return {"answer": "답변 생성 중 오류가 발생했습니다.", "sources": []}

    # 4단계: 응답 파싱
    try:
        result = json.loads(response_text.strip())
        return {
            "answer": result.get("answer", response_text),
            "sources": result.get("source_ids", source_ids[:5]),
        }
    except json.JSONDecodeError:
        return {
            "answer": response_text,
            "sources": source_ids[:5],
        }
