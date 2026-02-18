# TLDR AI Newsletter Manager
## Backend PRD — Claude Code 전용

> **Version 1.3** | February 2026 | Alpha 전략: 옵션 A (완전 무료)
> **GitHub:** github.com/qmakescl

---

## 개요 카드

| 항목 | 내용 |
|------|------|
| 담당 도구 | Claude Code |
| 언어/런타임 | Python 3.11+ / pip |
| AI 모델 (알파) | `gemini-2.5-flash-lite` — 무료 1,000 RPD |
| AI 모델 (정식) | `gemini-2.5-flash` — 환경 변수로 전환 |
| 최종 통합 | Claude Code (Frontend 빌드 병합 + Docker) |

---

## 1. 개요

Backend는 Gmail 연동, AI 처리(Gemini 2.5 Flash-Lite), 데이터 저장, REST API 서버, 통합 배포까지 전담한다. 알파 단계에서는 완전 무료 운영을 위해 `gemini-2.5-flash-lite`를 사용하며, 모델명은 `GEMINI_MODEL` 환경 변수로 분리하여 정식 전환 시 코드 수정 없이 업그레이드 가능하도록 설계한다.

---

## 2. 패키지 의존성

| 패키지 | 버전 | 용도 |
|--------|------|------|
| `google-api-python-client` | >=2.0 | Gmail API 연동 |
| `google-auth-oauthlib` | >=1.0 | OAuth 2.0 인증 |
| `google-genai` | >=1.0 | Gemini 2.5 Flash-Lite API |
| `fastapi` | >=0.100 | REST API 서버 |
| `uvicorn` | >=0.20 | ASGI 서버 |
| `chromadb` | >=0.4 | 벡터 DB (시맨틱 검색) |
| `apscheduler` | >=3.10 | 자동 동기화 스케줄러 |
| `beautifulsoup4` | >=4.12 | HTML 파싱 |
| `pydantic` | >=2.0 | 데이터 검증 / API 스키마 |
| `python-dotenv` | >=1.0 | 환경 변수 관리 |

**설치 명령어:**
```bash
pip install google-api-python-client google-auth-oauthlib google-genai \
            fastapi uvicorn chromadb apscheduler beautifulsoup4 \
            pydantic python-dotenv
```

---

## 3. Phase별 구현 요구사항

### Phase 1 — Gmail 연동 & 파서

#### 3.1.1 인증

- Google Cloud Console에서 OAuth 2.0 클라이언트 자격증명 발급
- `credentials.json` 로컬 저장, `token.json` 자동 갱신
- 필요 스코프: `gmail.readonly`

#### 3.1.2 메일 수집

- 발신자 필터: `from:@tldr.tech`
- 수집 기간: 최근 30일 (초기), 이후 증분 동기화
- 중복 방지: Gmail Message-ID를 SQLite에 기록

#### 3.1.3 파서

- HTML 이메일 파싱: BeautifulSoup4 사용
- 추출 항목: 기사 제목, 영문 요약(1-2문장), 원문 URL
- 파싱 실패 시 raw 텍스트 fallback 처리

#### 3.1.4 Newsletter 테이블 (날짜 인덱스)

메일 1통(1일치 뉴스레터)을 별도 `newsletters` 테이블로 관리하여 날짜 기반 조회를 지원한다.

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | `string` | UUID |
| `email_id` | `string` | Gmail Message-ID |
| `published_date` | `date` | 발행 날짜 (`YYYY-MM-DD`) |
| `article_count` | `integer` | 포함 기사 수 |
| `created_at` | `datetime` | 수집 시각 |

- `articles` 테이블에 `newsletter_id` 외래키(FK) 추가
- `GET /api/newsletters`: `published_date` DESC 정렬, 날짜별 `article_count` 및 `selectable` 플래그 반환
- `GET /api/articles?dates=2026-02-18,2026-02-17`: 복수 날짜 `IN` 쿼리로 합산 조회, `published_at` DESC 정렬

---

### Phase 2 — Gemini 2.5 Flash-Lite 처리 (옵션 A: 완전 무료)

#### 3.2.1 모델 설정

| 항목 | 값 |
|------|----|
| 알파 모델 코드 | `gemini-2.5-flash-lite` |
| 정식 모델 코드 | `gemini-2.5-flash` (환경 변수 전환) |
| 환경 변수 | `GEMINI_MODEL=gemini-2.5-flash-lite` |
| SDK | `google-genai` (최신 Gen AI SDK) |
| 임베딩 모델 | `text-embedding-004` (무료 1,000 RPD) |
| 배치 처리 | 기사 5개 단위 (1 API 호출 → 무료 한도 최적화) |
| 무료 한도 | 1,000 RPD — TLDR AI 1통 처리 시 약 4~5회 호출 |

**코드 예시:**
```python
from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

response = client.models.generate_content(
    model=model,
    contents="다음 AI 기사 5개를 분류·요약해줘: ..."
)
```

#### 3.2.2 무료 한도 보호 로직

- **처리 전 DB 확인:** `email_id`로 기처리 기사 건너뜀 (핵심 절약 포인트)
- **배치 API 호출:** 5개 기사 → JSON 배열로 묶어 단일 프롬프트 전송
- **지수 백오프:** 429 에러 시 자동 재시도 (1s → 2s → 4s)
- **일일 호출 카운터:** DB에 API 호출 수 기록, 한도 근접 시 로그 경고

#### 3.2.3 AI 처리 항목

- 카테고리 분류: `LLM`, `Vision`, `Agent`, `Tools`, `Policy`, `Research`, `Hardware`, `Other`
- 한국어 요약: 2-3문장, 핵심 내용 중심
- 중요도 스코어: 1(낮음) ~ 5(높음), 산업 영향력 기준
- 태그 추출: 최대 5개 키워드 (모델명, 기업명, 기술 용어 등)
- 벡터 임베딩 생성 및 ChromaDB 저장

---

### Phase 3 — REST API 서버

#### 3.3.1 FastAPI 앱 구조

```
backend/
├── app/
│   ├── main.py           # FastAPI 앱 진입점, CORS 설정
│   ├── routers/
│   │   ├── articles.py    # GET /api/articles, /api/articles/{id}
│   │   ├── newsletters.py # GET /api/newsletters  ← 캘린더 활성일 목록
│   │   ├── search.py      # GET /api/search
│   │   ├── chat.py        # POST /api/chat
│   │   └── sync.py        # POST /api/sync
│   ├── models/           # Pydantic 스키마 정의
│   └── services/
│       ├── gmail.py      # Gmail API 서비스
│       ├── gemini.py     # Gemini AI 서비스
│       ├── db.py         # SQLite DB 서비스
│       └── vector.py     # ChromaDB 벡터 서비스
├── static/               # Frontend 빌드 결과물 (통합 시 복사)
├── .env                  # 환경 변수 (gitignore)
├── .env.example          # 환경 변수 템플릿
└── requirements.txt
```

#### 3.3.2 CORS 설정

Antigravity 기본 포트(3000) 및 통합 후 정적 파일 서빙을 위해 설정.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Phase 4 — RAG 엔진 & 통합

#### 3.4.1 RAG 파이프라인

1. 사용자 질의 → Gemini Embedding → ChromaDB 유사 기사 검색 (top-k=10)
2. 검색된 기사 요약을 context로 Gemini 2.5 Flash-Lite에 전달
3. 답변 생성 시 출처 기사 ID 포함 (Frontend에서 링크 표시)

#### 3.4.2 통합 배포 (Claude Code 최종 작업)

1. Antigravity 빌드 산출물을 `backend/static/`에 복사
2. FastAPI `StaticFiles` 마운트 설정
3. 루트 경로(`/`)에서 `index.html` 서빙
4. `docker-compose.yml` 작성 (backend + chromadb 서비스)
5. `.env.example` 문서화

---

## 4. 환경 변수

| 변수명 | 필수 | 설명 |
|--------|------|------|
| `GEMINI_API_KEY` | 필수 | Google AI Studio API 키 |
| `GEMINI_MODEL` | 선택 | 기본값: `gemini-2.5-flash-lite` → 정식: `gemini-2.5-flash` |
| `GMAIL_CREDENTIALS_PATH` | 필수 | OAuth `credentials.json` 경로 |
| `DATABASE_URL` | 선택 | 기본값: `sqlite:///./tldr.db` |
| `CHROMA_PERSIST_DIR` | 선택 | 기본값: `./chroma_db` |
| `SYNC_SCHEDULE_HOUR` | 선택 | 자동 동기화 시간 (기본: `7`) |
| `CORS_ORIGINS` | 선택 | 기본값: `http://localhost:3000` |
| `DAILY_API_CALL_LIMIT` | 선택 | 일일 API 호출 경고 임계값 (기본: `900`) |

**`.env.example`:**
```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
GMAIL_CREDENTIALS_PATH=./credentials.json
DATABASE_URL=sqlite:///./tldr.db
CHROMA_PERSIST_DIR=./chroma_db
SYNC_SCHEDULE_HOUR=7
CORS_ORIGINS=http://localhost:3000
DAILY_API_CALL_LIMIT=900
```

---

## 5. Claude Code 첫 세션 권장 프롬프트

```
Gmail API를 사용해서 TLDR AI 뉴스레터 메일(from:@tldr.tech)을 가져오고,
각 기사의 제목/영문요약/URL을 파싱해서 SQLite에 저장하는 Python 스크립트를 만들어줘.
Google OAuth 2.0 인증 포함. Message-ID로 중복 방지 처리도 해줘.
환경: macOS (Apple Silicon), Python 3.11+, pip 패키지 사용.
```

---

*TLDR AI Newsletter Manager | Backend PRD v1.3 (Claude Code) | github.com/qmakescl*
