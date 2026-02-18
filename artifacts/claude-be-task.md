# Claude Code 작업 지시서 — Backend

> **프로젝트:** TLDR AI Newsletter Manager
> **담당:** Claude Code
> **기준 PRD:** `instructions/PRD_Backend_ClaudeCode_OptionA.md` v1.3

---

## 작업 배경

TLDR AI 뉴스레터를 Gmail에서 자동 수집하고, Gemini AI로 분류·요약하며, 시맨틱 검색 및 RAG 채팅을 제공하는 개인용 AI 뉴스 아카이브 시스템의 백엔드를 구현한다.

알파 단계에서는 완전 무료 운영을 위해 `gemini-2.5-flash-lite`를 사용하며, 환경 변수(`GEMINI_MODEL`)로 모델을 분리하여 정식 전환 시 코드 수정 없이 업그레이드 가능하도록 설계한다.

---

## 기술 스택

| 항목 | 선택 |
|------|------|
| 언어/런타임 | Python 3.12 |
| 패키지 관리 | uv |
| 가상환경 | `.venv` |
| API 프레임워크 | FastAPI + Uvicorn |
| 데이터베이스 | SQLite (python 내장 sqlite3) |
| 벡터 DB | ChromaDB (embedded) |
| AI 모델 | `gemini-2.5-flash-lite` (알파) / `gemini-2.5-flash` (정식) |
| 임베딩 모델 | `text-embedding-004` |
| 스케줄러 | APScheduler |
| HTML 파싱 | BeautifulSoup4 |

---

## 구현 범위 (4 Phase)

### Phase 1 — Gmail 연동 & 파서

- Google OAuth 2.0 인증 (`InstalledAppFlow`, `gmail.readonly` 스코프)
- `from:@tldr.tech` 필터로 최근 30일 이메일 수집, 이후 증분 동기화
- Gmail Message-ID로 SQLite에서 중복 방지
- BeautifulSoup4로 HTML 파싱: 기사 제목, 영문 요약, 원문 URL 추출
- 파싱 실패 시 plain text fallback
- DB 스키마:
  - `newsletters` 테이블: id(UUID), email_id(UNIQUE), published_date, article_count, created_at
  - `articles` 테이블: id, newsletter_id(FK), title, summary_en, summary_ko, url, category, tags, importance, published_at, email_id, ai_processed, created_at

### Phase 2 — Gemini AI 처리

- 5개 기사 단위 배치 처리 (API 호출 최소화)
- 처리 전 DB 확인으로 중복 API 호출 방지 (`ai_processed` 플래그)
- 429 에러 시 지수 백오프 (1s → 2s → 4s)
- 일일 API 호출 카운터 (`api_call_log` 테이블, 기본 한도 900)
- AI 처리 항목:
  - 카테고리: `LLM`, `Vision`, `Agent`, `Tools`, `Policy`, `Research`, `Hardware`, `Other`
  - 한국어 요약 (2-3문장)
  - 중요도 스코어 (1-5)
  - 태그 키워드 (최대 5개)
- `text-embedding-004`로 임베딩 생성 → ChromaDB 저장

### Phase 3 — REST API 서버

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/articles` | 기사 목록 (`?dates=`, `?category=`, `?page=`, `?size=`) |
| GET | `/api/articles/{id}` | 기사 상세 |
| GET | `/api/newsletters` | 뉴스레터 날짜 목록 (캘린더 UI용, published_date DESC) |
| GET | `/api/search?q=` | 시맨틱 검색 (ChromaDB top-10) |
| POST | `/api/chat` | RAG 채팅 (질의 → 검색 → Gemini 답변) |
| POST | `/api/sync` | 수동 Gmail 동기화 트리거 (BackgroundTasks) |

- CORS: `http://localhost:3000` (Frontend 개발 서버)
- 앱 시작 시 DB 자동 초기화 (`lifespan`)

### Phase 4 — RAG 엔진 & 통합

- RAG 파이프라인: 질의 임베딩 → ChromaDB top-10 → context 구성 → Gemini 답변 + 출처 기사 ID
- APScheduler로 매일 지정 시간에 증분 자동 동기화
- `backend/static/` 폴더에 프론트엔드 빌드 결과 배치 시 정적 파일 자동 서빙
- `Dockerfile`, `docker-compose.yml` (선택 사항, 서버 배포용)

---

## 필수 의존성

```
google-api-python-client>=2.0
google-auth-oauthlib>=1.0
google-genai>=1.0
fastapi>=0.100
uvicorn[standard]>=0.20
chromadb>=0.4
apscheduler>=3.10
beautifulsoup4>=4.12
pydantic>=2.0
pydantic-settings>=2.0
python-dotenv>=1.0
```

---

## 환경 변수

| 변수명 | 필수 | 기본값 |
|--------|------|--------|
| `GEMINI_API_KEY` | 필수 | — |
| `GEMINI_MODEL` | 선택 | `gemini-2.5-flash-lite` |
| `GMAIL_CREDENTIALS_PATH` | 필수 | `./credentials.json` |
| `DATABASE_URL` | 선택 | `sqlite:///./tldr.db` |
| `CHROMA_PERSIST_DIR` | 선택 | `./chroma_db` |
| `SYNC_SCHEDULE_HOUR` | 선택 | `7` |
| `CORS_ORIGINS` | 선택 | `http://localhost:3000` |
| `DAILY_API_CALL_LIMIT` | 선택 | `900` |

---

## 완료 조건

- [ ] `uv run python main.py`로 서버 정상 기동
- [ ] Gmail 동기화 실행 후 SQLite에 newsletters/articles 데이터 저장 확인
- [ ] AI 처리 실행 후 summary_ko, category, importance 필드 채워짐 확인
- [ ] `GET /api/articles` JSON 응답 확인
- [ ] `POST /api/chat` RAG 답변 + sources 배열 확인
- [ ] `report/claude_report_backend.md` 완료 리포트 저장 (.CLAUDE.md 규칙)
