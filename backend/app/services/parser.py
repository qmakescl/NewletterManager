"""TLDR AI 뉴스레터 HTML/텍스트 파서.

TLDR AI 뉴스레터의 구조:
- 섹션: HEADLINES & LAUNCHES, RESEARCH & INNOVATION, ENGINEERING & RESOURCES, MISCELLANEOUS
- 각 기사: 제목(링크), 읽기 시간, 1-2문장 영문 요약
"""

import logging
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SECTION_NAMES = [
    "HEADLINES & LAUNCHES",
    "RESEARCH & INNOVATION",
    "ENGINEERING & RESOURCES",
    "MISCELLANEOUS",
]


@dataclass
class ParsedArticle:
    title: str
    summary_en: str
    url: str | None
    section: str


def parse_tldr_email(html: str, plain_text: str = "") -> list[ParsedArticle]:
    """TLDR AI 뉴스레터를 파싱하여 기사 목록을 반환한다.

    HTML 파싱 실패 시 plain text fallback을 시도한다.
    """
    articles = _parse_html(html)
    if not articles and plain_text:
        logger.warning("HTML 파싱 결과 없음, plain text fallback 시도")
        articles = _parse_plain_text(plain_text)
    if not articles:
        logger.error("HTML 및 plain text 파싱 모두 실패")
    return articles


def _parse_html(html: str) -> list[ParsedArticle]:
    """TLDR 뉴스레터 HTML에서 기사를 추출한다.

    TLDR 이메일은 테이블 기반 레이아웃을 사용한다.
    주요 패턴: 굵은 링크(기사 제목) + 읽기 시간 표시 → 다음 텍스트 블록(요약)
    """
    soup = BeautifulSoup(html, "html.parser")
    articles: list[ParsedArticle] = []

    current_section = "Other"

    # 모든 텍스트 콘텐츠를 순회하며 섹션 헤더와 기사를 찾는다
    all_text_elements = soup.find_all(["td", "div", "p", "span", "a", "b", "strong"])

    i = 0
    while i < len(all_text_elements):
        elem = all_text_elements[i]
        text = elem.get_text(strip=True)

        # 섹션 헤더 감지
        for section_name in SECTION_NAMES:
            if section_name in text.upper():
                current_section = section_name
                break

        # 기사 제목 패턴 감지: 링크가 있는 굵은 텍스트 + "MINUTE READ"
        if elem.name in ("a", "b", "strong"):
            link = None
            title_text = text

            # 링크 추출
            if elem.name == "a" and elem.get("href"):
                link = elem["href"]
            elif elem.find("a"):
                a_tag = elem.find("a")
                link = a_tag.get("href", "")
                title_text = a_tag.get_text(strip=True) or title_text

            # "MINUTE READ" 패턴으로 기사 여부 확인
            # 제목 근처에서 MINUTE READ를 찾는다
            context_text = ""
            parent = elem.parent
            if parent:
                context_text = parent.get_text(strip=True)

            if not title_text or len(title_text) < 5:
                i += 1
                continue

            is_article = False
            if re.search(r"\d+\s*MINUTE\s*READ", context_text, re.IGNORECASE):
                is_article = True
            elif link and "tldr.tech" not in (link or "") and title_text and len(title_text) > 10:
                # 외부 링크면서 충분한 길이의 제목이면 기사로 간주
                # (TLDR 내부 링크 제외)
                pass

            if is_article and link:
                # 제목에서 "(N MINUTE READ)" 부분 제거
                clean_title = re.sub(
                    r"\s*\(\d+\s*MINUTE\s*READ\)\s*", "", title_text, flags=re.IGNORECASE
                ).strip()

                if not clean_title:
                    i += 1
                    continue

                # 요약 추출: 제목 이후 텍스트 블록에서 찾기
                summary = _extract_summary_after(elem)

                if clean_title and not _is_duplicate(articles, clean_title):
                    articles.append(ParsedArticle(
                        title=clean_title,
                        summary_en=summary,
                        url=_clean_url(link),
                        section=current_section,
                    ))
        i += 1

    logger.info("HTML 파싱 완료: %d개 기사 추출", len(articles))
    return articles


def _extract_summary_after(elem) -> str:
    """기사 제목 요소 이후의 요약 텍스트를 추출한다."""
    summary_parts: list[str] = []

    # 부모의 다음 형제 또는 같은 셀 내 다음 텍스트를 찾는다
    parent = elem.parent
    if parent is None:
        return ""

    # 현재 요소 이후의 텍스트를 수집
    found_elem = False
    for child in parent.descendants:
        if child == elem:
            found_elem = True
            continue
        if found_elem and hasattr(child, "string") and child.string:
            text = child.string.strip()
            # MINUTE READ 패턴은 건너뛴다
            if re.search(r"\d+\s*MINUTE\s*READ", text, re.IGNORECASE):
                continue
            # 다른 섹션 헤더를 만나면 중단
            if any(s in text.upper() for s in SECTION_NAMES):
                break
            if text and len(text) > 10:
                summary_parts.append(text)
                break

    # 부모의 다음 형제에서도 찾기
    if not summary_parts:
        next_sib = parent.find_next_sibling()
        if next_sib:
            text = next_sib.get_text(strip=True)
            if text and len(text) > 10 and not re.search(
                r"\d+\s*MINUTE\s*READ", text, re.IGNORECASE
            ):
                summary_parts.append(text)

    return " ".join(summary_parts).strip()


def _parse_plain_text(text: str) -> list[ParsedArticle]:
    """TLDR 뉴스레터 plain text 버전에서 기사를 추출한다.

    예상 형식:
        SECTION NAME
        Article Title (N MINUTE READ)
        https://...
        Summary text paragraph.
    """
    articles: list[ParsedArticle] = []
    lines = text.strip().split("\n")
    current_section = "Other"

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 섹션 헤더 감지
        for section_name in SECTION_NAMES:
            if section_name in line.upper():
                current_section = section_name
                break

        # 기사 제목 패턴: "Title (N MINUTE READ)"
        match = re.match(r"^(.+?)\s*\((\d+)\s*MINUTE\s*READ\)\s*$", line, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            url = None
            summary = ""

            # 다음 줄에서 URL 찾기
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if re.match(r"https?://", next_line):
                    url = next_line
                    i += 1

            # 그 다음 줄에서 요약 찾기
            summary_lines: list[str] = []
            j = i + 1
            while j < len(lines):
                sline = lines[j].strip()
                if not sline:
                    break
                if re.match(r"^(.+?)\s*\(\d+\s*MINUTE\s*READ\)\s*$", sline, re.IGNORECASE):
                    break
                if any(s in sline.upper() for s in SECTION_NAMES):
                    break
                summary_lines.append(sline)
                j += 1

            summary = " ".join(summary_lines).strip()

            if title and not _is_duplicate(articles, title):
                articles.append(ParsedArticle(
                    title=title,
                    summary_en=summary,
                    url=url,
                    section=current_section,
                ))
        i += 1

    logger.info("Plain text 파싱 완료: %d개 기사 추출", len(articles))
    return articles


def _clean_url(url: str) -> str:
    """TLDR 트래킹 래퍼를 제거하고 원본 URL을 추출한다."""
    # TLDR은 종종 트래킹 URL을 사용한다
    # 예: https://tracking.tldr.tech/...?redirect=actual_url
    if "redirect=" in url:
        match = re.search(r"redirect=([^&]+)", url)
        if match:
            from urllib.parse import unquote
            return unquote(match.group(1))
    return url


def _is_duplicate(articles: list[ParsedArticle], title: str) -> bool:
    """이미 추출된 기사와 중복인지 확인한다."""
    return any(a.title == title for a in articles)
