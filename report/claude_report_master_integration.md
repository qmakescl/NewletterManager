# Claude Code 완료 리포트 — 마스터 통합

> **작업:** Frontend + Backend 통합 연결 및 최종 완성
> **기준 계획:** `artifacts/master-task.md`, `artifacts/master-implementation_plan.md`
> **완료일:** 2026-02-18

---

## 작업 요약

Backend(FastAPI + Gemini + Gmail)와 Frontend(React + Vite)를 독립 구현 상태에서 단일 배포 가능한 시스템으로 통합 완료.

---

## 수행 Phase 별 결과

### Phase M0 — API 계약 수정 ✅

**문제:** Frontend가 `GET /api/categories`를 호출하나 Backend에 해당 엔드포인트가 없었음.

**수행 내용:**

| 파일 | 변경 유형 | 설명 |
|------|-----------|------|
| `backend/app/models/category.py` | 신규 생성 | `CategoryItem(name, count)` Pydantic 모델 |
| `backend/app/services/db.py` | 함수 추가 | `get_categories()` — articles 테이블에서 category DISTINCT + COUNT 집계 |
| `backend/app/routers/categories.py` | 신규 생성 | `GET /api/categories` 라우터 |
| `backend/app/main.py` | import 추가 + 라우터 등록 | `categories.router` 를 `/api` prefix로 등록 |

**응답 형식:**
```json
[
  { "name": "LLM", "count": 12 },
  { "name": "Tools", "count": 8 }
]
```

### Phase M1 — Frontend-Backend 통합 연결 ✅

**문제:** `frontend/.env.development`에 `VITE_USE_MOCK=true`로 실제 API 미연결 상태.

**수행 내용:**

| 파일 | 변경 전 | 변경 후 |
|------|---------|---------|
| `frontend/.env.development` | `VITE_API_BASE_URL=http://localhost:8000` / `VITE_USE_MOCK=true` | `VITE_API_BASE_URL=` (빈값) / `VITE_USE_MOCK=false` |

**설계 근거:**
- `VITE_API_BASE_URL=''`: 빈값으로 설정하면 Vite 개발 서버의 `/api` 프록시(`vite.config.js`)가 `localhost:8000`으로 요청을 중계. CORS 문제 없음.
- `VITE_USE_MOCK=false`: Mock 데이터 대신 실제 Backend API 호출.

### Phase M2 — 빌드 통합 스크립트 ✅

**신규 생성:** `scripts/build_and_deploy.sh`

로컬 환경에서 Frontend를 빌드하고 Backend의 `static/` 디렉토리로 복사하는 자동화 스크립트:

```bash
# 실행 방법
bash scripts/build_and_deploy.sh

# 이후 단일 서버 실행
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

**동작 순서:**
1. `frontend/` 에서 `npm install`
2. `npm run build` → `frontend/dist/` 생성
3. `backend/static/` 초기화 후 `dist/` 내용 복사

FastAPI `main.py`의 StaticFiles 조건부 마운트 코드가 `backend/static/`에 파일이 있을 때 자동 활성화됨.

### Phase M3 — Docker 멀티스테이지 빌드 ✅

**수정 파일:** `Dockerfile`

기존 단일 Python 스테이지에서 멀티스테이지 빌드로 변경:

```
Stage 1 (node:20-slim)   → Frontend npm ci + npm run build → dist/
Stage 2 (python:3.12-slim) → Backend 의존성 + 소스 + dist/ 복사 → 서버 실행
```

**효과:**
- 최종 이미지에 Node.js 런타임 미포함 → 이미지 경량화
- `COPY --from=frontend-builder /frontend/dist ./backend/static/` 로 빌드 산출물 주입

### Phase M4 — 문서화 ✅

**신규 생성:** `.env.example` — Backend + Frontend 통합 환경 변수 설명 및 기본값 문서화

---

## 최종 API 엔드포인트 목록

| 메서드 | 경로 | 기능 |
|--------|------|------|
| GET | `/api/articles` | 기사 목록 (날짜/카테고리 필터, 페이지네이션) |
| GET | `/api/articles/{id}` | 기사 상세 조회 |
| GET | `/api/newsletters` | 캘린더용 뉴스레터 날짜 목록 |
| GET | `/api/categories` | 카테고리별 기사 수 **(신규)** |
| GET | `/api/search?q=` | 시맨틱 검색 (ChromaDB) |
| POST | `/api/chat` | RAG 채팅 (Gemini) |
| POST | `/api/sync` | Gmail 동기화 트리거 |

---

## 변경 파일 목록

### 신규 생성

| 파일 | 설명 |
|------|------|
| `backend/app/models/category.py` | CategoryItem Pydantic 모델 |
| `backend/app/routers/categories.py` | GET /api/categories 라우터 |
| `scripts/build_and_deploy.sh` | 빌드 통합 자동화 스크립트 |
| `.env.example` | 환경 변수 예시 및 설명 |

### 수정

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/services/db.py` | `get_categories()` 함수 추가 |
| `backend/app/main.py` | categories 라우터 import 및 등록 |
| `frontend/.env.development` | `VITE_USE_MOCK=false`, `VITE_API_BASE_URL=''` |
| `Dockerfile` | 멀티스테이지 빌드 (Node.js + Python) |

---

## 완료 조건 체크

- [x] `GET /api/categories` 엔드포인트 추가 (카테고리명 + 기사 수 반환)
- [x] Frontend Mock 모드 해제 → Backend API 직접 연동 설정
- [x] `scripts/build_and_deploy.sh` 실행으로 `backend/static/` 생성 → 단일 서버 서빙 가능
- [x] Dockerfile 멀티스테이지 빌드 → `docker compose up --build`로 컨테이너 실행 가능
- [x] `.env.example` 통합 환경 변수 문서화

---

## 로컬 개발 실행 방법

```bash
# Backend 실행 (가상환경 활성화 필요)
source .venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000

# Frontend 개발 서버 (별도 터미널)
cd frontend && npm run dev
# → http://localhost:3000 에서 접근, /api 는 localhost:8000으로 프록시
```

## 프로덕션 배포 방법

### 방법 1: 로컬 빌드 후 단일 서버

```bash
bash scripts/build_and_deploy.sh
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
# → http://localhost:8000 에서 API + Frontend 통합 서빙
```

### 방법 2: Docker Compose

```bash
# backend/.env 파일 준비 (cp .env.example backend/.env 후 값 입력)
docker compose up --build
# → http://localhost:8000 에서 접근
```

---

## 주의 사항

- Gmail OAuth 인증: 최초 실행 전 `credentials.json` 발급 및 배치 필요
- Gemini API Key: `backend/.env`에 `GEMINI_API_KEY` 설정 필요
- SQLite DB 및 ChromaDB 데이터는 Docker 볼륨(`app_data`, `chroma_data`)에 영속 저장
