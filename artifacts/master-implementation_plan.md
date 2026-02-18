# Master 구현 계획서 — 전체 통합 & 완성

> **프로젝트:** TLDR AI Newsletter Manager
> **작성일:** 2026-02-18
> **PRD 버전:** v1.3 Master (옵션 A — 완전 무료)
> **선행 문서:** `claude-be-implementation_plan.md`, `gemini-implementation_plan.md`

---

## 수정/생성 파일 전체 요약

### 수정 파일 (6개)

| 파일 | Phase | 수정 내용 |
|------|-------|-----------|
| `backend/app/main.py` | M0 | categories 라우터 등록 추가 |
| `backend/app/services/db.py` | M0 | `get_categories()` 함수 추가 |
| `frontend/.env.development` | M1 | `VITE_USE_MOCK=false` 전환 |
| `frontend/src/api/client.js` | M1 | Vite proxy 활용을 위한 BASE_URL 조정 (필요 시) |
| `Dockerfile` | M3 | 멀티스테이지 빌드 (Node.js + Python) |
| `docker-compose.yml` | M3 | frontend 빌드 통합 반영 |

### 생성 파일 (5개)

| 파일 | Phase | 설명 |
|------|-------|------|
| `backend/app/routers/categories.py` | M0 | GET /api/categories 엔드포인트 |
| `backend/app/models/category.py` | M0 | CategoryItem Pydantic 모델 |
| `scripts/build_and_deploy.sh` | M2 | Frontend 빌드 → backend/static 복사 자동화 |
| `.env.example` (루트) | M4 | 통합 환경 변수 템플릿 |
| `report/claude_report_master_integration.md` | M4 | 완료 리포트 |

---

## 구현 순서 (Phase M0 → M4)

### Phase M0 — API 계약 수정 (Gap Fix)

#### M0.1 — CategoryItem Pydantic 모델 생성

**파일:** `backend/app/models/category.py` (신규)

```python
from pydantic import BaseModel


class CategoryItem(BaseModel):
    name: str
    count: int


class CategoryListResponse(BaseModel):
    categories: list[CategoryItem]
```

**Frontend 기대 형식과 대조:**
- Frontend `mockCategories`: `[{ name: "LLM", count: 12 }, ...]` — 배열 직접 반환
- 결정: Frontend client.js가 응답을 그대로 사용하므로, **배열 직접 반환** 방식 채택
- `fetchCategories()` 반환값이 배열이므로 `response_model=list[CategoryItem]` 사용

---

#### M0.2 — `get_categories()` DB 함수 추가

**파일:** `backend/app/services/db.py` (수정 — 함수 추가)

```python
def get_categories() -> list[dict[str, Any]]:
    """articles 테이블에서 카테고리별 기사 수를 집계한다."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT category AS name, COUNT(*) AS count
               FROM articles
               GROUP BY category
               ORDER BY count DESC"""
        ).fetchall()
    return [dict(row) for row in rows]
```

**핵심 포인트:**
- GROUP BY로 카테고리별 기사 수 집계
- count DESC 정렬 (가장 많은 카테고리가 상단)
- articles 테이블의 category 인덱스(`idx_articles_category`) 활용

---

#### M0.3 — Categories 라우터 생성

**파일:** `backend/app/routers/categories.py` (신규)

```python
from fastapi import APIRouter

from backend.app.models.category import CategoryItem
from backend.app.services.db import get_categories

router = APIRouter(tags=["categories"])


@router.get("/categories", response_model=list[CategoryItem])
def list_categories():
    """카테고리 목록과 각 카테고리별 기사 수를 반환한다."""
    return get_categories()
```

---

#### M0.4 — FastAPI 앱에 라우터 등록

**파일:** `backend/app/main.py` (수정)

변경 사항:
```python
# 기존
from backend.app.routers import articles, chat, newsletters, search, sync

# 변경
from backend.app.routers import articles, categories, chat, newsletters, search, sync

# 라우터 등록 추가
app.include_router(categories.router, prefix="/api")
```

---

**Phase M0 파일 의존 관계:**
```
models/category.py → services/db.py (get_categories) → routers/categories.py → app/main.py
```

**Phase M0 검증:**
```bash
uv run uvicorn backend.app.main:app --reload --port 8000
curl http://localhost:8000/api/categories
# 기대: [{"name":"LLM","count":12},{"name":"Agent","count":8},...] (DB에 데이터 존재 시)
# 빈 DB: [] (정상)
```

---

### Phase M1 — Frontend-Backend 통합 연결

#### M1.1 — Frontend Mock 모드 비활성화

**파일:** `frontend/.env.development` (수정)

```env
VITE_API_BASE_URL=
VITE_USE_MOCK=false
```

**핵심 결정:**
- `VITE_API_BASE_URL`을 빈 값으로 변경 → Vite dev proxy 사용 (`/api` → `localhost:8000`)
- 기존 `http://localhost:8000` 직접 지정 시 CORS 이슈 가능 → proxy 경유가 안전
- `client.js`의 `const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''`에서 빈 값 = 상대 경로 → proxy 활용

#### M1.2 — API 통합 테스트 매트릭스

개발 환경에서 Backend + Frontend 동시 실행 후 검증:

| # | API 호출 | Frontend 컴포넌트 | 검증 항목 |
|---|----------|-------------------|-----------|
| 1 | `GET /api/newsletters` | NewsletterCalendar | 캘린더에 활성 날짜 표시 |
| 2 | `GET /api/categories` | CategoryFilter | 사이드바에 카테고리 목록 + 기사 수 표시 |
| 3 | `GET /api/articles?dates=...` | ArticleList | 날짜 선택 시 기사 카드 그리드 표시 |
| 4 | `GET /api/articles?category=LLM` | ArticleList | 카테고리 필터 적용 |
| 5 | `GET /api/articles/{id}` | ArticleDetail | 카드 클릭 시 상세 패널 표시 |
| 6 | `GET /api/search?q=GPT` | SearchBar → ArticleList | 검색 결과 카드 표시 |
| 7 | `POST /api/chat` | ChatPanel | RAG 답변 + 출처 기사 링크 |
| 8 | `POST /api/sync` | SyncStatus | 동기화 트리거 → 스피너 → 완료 |

**실행 방법:**
```bash
# 터미널 1: Backend
uv run python main.py

# 터미널 2: Frontend (dev server with proxy)
cd frontend && npm run dev
```

브라우저에서 `http://localhost:3000` 접속하여 위 8개 시나리오 수동 확인.

#### M1.3 — 에러 핸들링 보강 (필요 시)

통합 테스트 중 발견되는 이슈에 따라:
- CORS 추가 설정 (Backend `CORS_ORIGINS`에 `http://localhost:3000` 확인)
- API 응답 형식 불일치 수정
- 에러 상태 Toast 메시지 조정

---

### Phase M2 — 빌드 통합 & 정적 파일 서빙

#### M2.1 — Frontend 프로덕션 빌드

```bash
cd frontend
npm run build
# → dist/index.html, dist/assets/main-xxx.js, dist/assets/main-xxx.css
```

빌드 시 `.env.production` 적용:
```env
VITE_API_BASE_URL=     # 빈 값 → 상대 경로 → FastAPI 동일 서버에서 서빙
VITE_USE_MOCK=false
```

#### M2.2 — 빌드 산출물 → backend/static/ 복사

```bash
# backend/static/ 디렉토리 비우고 복사
rm -rf backend/static/*
cp -r frontend/dist/* backend/static/
```

#### M2.3 — 빌드 자동화 스크립트

**파일:** `scripts/build_and_deploy.sh` (신규)

```bash
#!/bin/bash
set -e

echo "=== Frontend 빌드 ==="
cd "$(dirname "$0")/../frontend"
npm run build

echo "=== backend/static/ 복사 ==="
STATIC_DIR="$(dirname "$0")/../backend/static"
mkdir -p "$STATIC_DIR"
rm -rf "$STATIC_DIR"/*
cp -r dist/* "$STATIC_DIR"/

echo "=== 통합 완료 ==="
echo "서버 실행: uv run python main.py"
echo "접속: http://localhost:8000"
```

#### M2.4 — 단일 서버 통합 서빙 확인

```bash
uv run python main.py
# http://localhost:8000      → Frontend UI (index.html)
# http://localhost:8000/api/ → Backend API
```

**확인 항목:**
- `http://localhost:8000` → index.html 정상 렌더링
- `/api/articles` → JSON API 응답 정상
- SPA 라우팅: 브라우저 새로고침 시 index.html fallback (`html=True`)

**FastAPI 코드 확인 (이미 구현됨):**
```python
# backend/app/main.py (기존 코드)
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.is_dir() and any(_static_dir.iterdir()):
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
```

⚠️ **주의:** StaticFiles가 `/`에 마운트되므로, API 라우터(`/api/*`)가 먼저 등록되어야 함. 현재 코드에서 `include_router`가 `app.mount`보다 위에 있으므로 정상.

---

### Phase M3 — Docker 통합 배포

#### M3.1 — Dockerfile 멀티스테이지 빌드

**파일:** `Dockerfile` (수정)

```dockerfile
# === Stage 1: Frontend 빌드 ===
FROM node:20-slim AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# === Stage 2: Backend + 정적 파일 ===
FROM python:3.12-slim

WORKDIR /app

# Python 의존성
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system .

# Backend 소스
COPY backend/ ./backend/
COPY main.py .

# Frontend 빌드 산출물 → static/
COPY --from=frontend-builder /frontend/dist ./backend/static/

# 데이터 디렉토리
RUN mkdir -p /app/data /app/chroma_db

ENV DATABASE_URL=sqlite:////app/data/tldr.db
ENV CHROMA_PERSIST_DIR=/app/chroma_db

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**변경 포인트:**
- Node.js 스테이지 추가 (Frontend 빌드)
- `COPY --from=frontend-builder`로 빌드 산출물만 최종 이미지에 포함
- 최종 이미지에 Node.js 불포함 → 경량 유지

#### M3.2 — docker-compose.yml 확인

**파일:** `docker-compose.yml` (수정 — 필요 시)

기존 구조 유지. Dockerfile이 멀티스테이지로 변경되므로 docker-compose는 큰 변경 불필요.
`frontend/` 디렉토리가 빌드 컨텍스트에 포함되어야 하므로 context가 `.` (루트)인 점 확인.

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    # ... (기존 설정 유지)
```

#### M3.3 — Docker 빌드 & 실행 테스트

```bash
docker compose build
docker compose up -d

# 확인
curl http://localhost:8000/api/categories
curl http://localhost:8000/         # Frontend UI
```

---

### Phase M4 — 최종 검증 & 문서화

#### M4.1 — E2E 스모크 테스트 체크리스트

**사전 조건:** Google OAuth 설정 완료 (`credentials.json` + `token.json`)

| # | 테스트 시나리오 | 기대 결과 |
|---|----------------|-----------|
| 1 | `POST /api/sync` 호출 | Gmail에서 TLDR AI 메일 수집 → DB 저장 |
| 2 | DB에 newsletters/articles 데이터 확인 | SQLite에 레코드 존재 |
| 3 | AI 처리 후 `summary_ko`, `category`, `importance` 확인 | 빈 값 아닌 데이터 채워짐 |
| 4 | `GET /api/newsletters` | 캘린더용 날짜 목록 반환 |
| 5 | `GET /api/categories` | 카테고리별 기사 수 반환 |
| 6 | `GET /api/articles?dates=2026-02-18` | 해당 날짜 기사 목록 반환 |
| 7 | `GET /api/search?q=GPT` | 시맨틱 검색 결과 반환 |
| 8 | `POST /api/chat` (RAG 질의) | 답변 + 출처 기사 ID 반환 |
| 9 | 브라우저 `http://localhost:8000` 접속 | Frontend UI 정상 렌더링 |
| 10 | UI에서 캘린더 날짜 선택 → 기사 카드 표시 | 실제 데이터 기반 UI 동작 |

#### M4.2 — 루트 `.env.example` 통합 템플릿

**파일:** `.env.example` (루트, 신규)

통합 배포 시 참조용. `backend/.env.example`과 동일 내용이나 루트에 통합 제공.

```env
# === Backend (필수) ===
GEMINI_API_KEY=your_api_key_here
GMAIL_CREDENTIALS_PATH=./credentials.json

# === Backend (선택) ===
GEMINI_MODEL=gemini-2.5-flash-lite
DATABASE_URL=sqlite:///./tldr.db
CHROMA_PERSIST_DIR=./chroma_db
SYNC_SCHEDULE_HOUR=7
CORS_ORIGINS=http://localhost:3000
DAILY_API_CALL_LIMIT=900
```

#### M4.3 — 완료 리포트

**파일:** `report/claude_report_master_integration.md`

내용:
- 통합 작업 요약 (Gap 수정, 빌드 통합, Docker)
- 수정/생성 파일 목록
- E2E 테스트 결과
- 남은 작업 (사용자 OAuth 설정 등)

---

## 전체 파일 영향도 맵

```
NewletterManager/
├── backend/
│   ├── app/
│   │   ├── main.py                  ← [수정] M0: categories 라우터 등록
│   │   ├── models/
│   │   │   └── category.py          ← [신규] M0: CategoryItem 모델
│   │   ├── routers/
│   │   │   └── categories.py        ← [신규] M0: GET /api/categories
│   │   └── services/
│   │       └── db.py                ← [수정] M0: get_categories() 추가
│   └── static/                      ← [복사] M2: Frontend 빌드 산출물
├── frontend/
│   └── .env.development             ← [수정] M1: VITE_USE_MOCK=false
├── scripts/
│   └── build_and_deploy.sh          ← [신규] M2: 빌드 자동화
├── Dockerfile                       ← [수정] M3: 멀티스테이지 빌드
├── docker-compose.yml               ← [수정] M3: 필요 시 조정
├── .env.example                     ← [신규] M4: 루트 통합 템플릿
└── report/
    └── claude_report_master_integration.md  ← [신규] M4: 완료 리포트
```

**총 수정: 6개 파일 / 총 신규: 5개 파일**

---

## 주요 설계 결정

| 결정 사항 | 선택 | 이유 |
|-----------|------|------|
| `/api/categories` 응답 형식 | `list[CategoryItem]` (배열 직접) | Frontend mockData와 동일 형식, 별도 wrapper 불필요 |
| Frontend dev 환경 API 연결 | Vite proxy (`BASE_URL=''`) | CORS 우회, 개발 편의성 |
| 빌드 통합 방식 | `dist/` → `backend/static/` 복사 | PRD §7.1 명시, FastAPI StaticFiles 활용 |
| Docker 빌드 | 멀티스테이지 (Node + Python) | 최종 이미지에 Node.js 불포함, 경량화 |
| 정적 파일 마운트 순서 | API 라우터 먼저, StaticFiles 마지막 | `/api/*` 우선 매칭 보장 |
| SPA fallback | `StaticFiles(html=True)` | 존재하지 않는 경로 → index.html 반환 |

---

## Phase별 예상 작업량

| Phase | 작업 | 수정/생성 파일 수 |
|-------|------|-------------------|
| M0 | API Gap 수정 | 4개 (모델 1 + DB 1 + 라우터 1 + main 1) |
| M1 | Frontend 연동 전환 | 1~2개 (.env + client.js 필요 시) |
| M2 | 빌드 통합 | 1개 스크립트 + static/ 복사 |
| M3 | Docker 멀티스테이지 | 1~2개 (Dockerfile + compose) |
| M4 | 검증 & 문서화 | 2개 (.env.example + 리포트) |
| **합계** | | **~11개 파일** |
