# Master 작업 지시서 — 전체 통합 & 완성

> **프로젝트:** TLDR AI Newsletter Manager
> **담당:** Claude Code (통합 총괄)
> **기준 PRD:** `instructions/PRD_Master_OptionA.md` v1.3
> **선행 완료:** Backend 구현 완료 / Frontend 구현 완료 (Mock 데이터 기반)

---

## 작업 배경

Backend(FastAPI + Gemini + Gmail)와 Frontend(React + Vite)가 **각각 독립적으로 구현 완료**된 상태다. 이제 Master PRD §7 "통합 & 배포"에 따라 두 시스템을 연결하고, API 계약 불일치를 수정하며, 단일 서버로 통합 배포할 수 있는 최종 완성 상태로 만드는 것이 목표다.

---

## 현재 상태 요약

| 구성 요소 | 상태 | 비고 |
|-----------|------|------|
| Backend (FastAPI) | ✅ 구현 완료 | Phase 0-4 전체 완료 |
| Frontend (React) | ✅ 구현 완료 | Mock 데이터 기반, 빌드 산출물 존재 (`dist/`) |
| API 계약 일치 | ⚠️ 부분 불일치 | `GET /api/categories` 누락, 응답 스키마 세부 차이 |
| 통합 서빙 | ❌ 미연결 | `backend/static/` 비어 있음 |
| Docker 통합 | ⚠️ 부분 완료 | Dockerfile에 Frontend 빌드 미포함 |
| E2E 검증 | ❌ 미수행 | 전 구간 통합 테스트 필요 |

---

## Gap 분석 결과

### GAP-1: `GET /api/categories` 엔드포인트 누락 (Critical)

- **Frontend:** `fetchCategories()` → `GET /api/categories` 호출
- **Backend:** 해당 라우터 없음 (`routers/` 에 categories.py 미존재)
- **PRD 근거:** Master PRD §4.1에 `GET /api/categories` 명시
- **필요 응답 형식:** `[{ "name": "LLM", "count": 12 }, ...]`

### GAP-2: Frontend Mock 모드 활성 상태

- `.env.development`에 `VITE_USE_MOCK=true` — 실제 API 미연결
- 통합 테스트를 위해 `false`로 전환 후 API 호출 정상 확인 필요

### GAP-3: 정적 파일 통합 미완료

- `frontend/dist/` 빌드 산출물 존재하나 `backend/static/`로 미복사
- FastAPI의 `StaticFiles` 마운트 코드는 준비됨 (빈 디렉토리 감지 조건부 마운트)

### GAP-4: Dockerfile Frontend 미포함

- 현재 Dockerfile은 `backend/`와 `main.py`만 복사
- Frontend Node.js 빌드 → `static/` 복사 → Python 서버 실행의 멀티스테이지 빌드 필요

### GAP-5: `/api/sync` 응답 형식 미세 차이

- Backend 반환: `{ "status": "sync_started", "message": "..." }`
- Frontend Mock: `{ "status": "success", "message": "Sync completed" }`
- Frontend client.js에서 `response.ok`만 확인하므로 동작에 영향 없음 (Low)

---

## 구현 범위 (5 Phase)

### Phase M0 — API 계약 수정 (Gap Fix)

- Backend: `GET /api/categories` 엔드포인트 추가
  - `routers/categories.py`: articles 테이블에서 DISTINCT category + COUNT 집계
  - `models/category.py`: CategoryItem Pydantic 모델
  - `services/db.py`: `get_categories()` 함수 추가
  - `app/main.py`: categories 라우터 등록
- Backend: `/api/search` 응답에 `selected_dates` 필드 일관성 확인

### Phase M1 — Frontend-Backend 통합 연결

- Frontend `.env.development` → `VITE_USE_MOCK=false` 전환
- 개발 환경에서 Vite proxy (`/api` → `localhost:8000`) 경유 API 호출 확인
- 7개 API 엔드포인트 통합 동작 확인:
  - `GET /api/articles` (날짜/카테고리 필터, 페이지네이션)
  - `GET /api/articles/{id}` (상세 조회)
  - `GET /api/newsletters` (캘린더 활성일)
  - `GET /api/categories` (카테고리 목록 + 기사 수)
  - `GET /api/search?q=` (시맨틱 검색)
  - `POST /api/chat` (RAG 채팅)
  - `POST /api/sync` (Gmail 동기화 트리거)

### Phase M2 — 빌드 통합 & 정적 파일 서빙

- Frontend 프로덕션 빌드: `npm run build` → `dist/`
- 빌드 산출물 복사: `dist/*` → `backend/static/`
- FastAPI 단일 서버에서 API + 정적 파일 동시 서빙 확인
- SPA 라우팅 정상 동작 확인 (`html=True` 옵션)
- 빌드 통합 자동화 스크립트 작성 (`scripts/build_and_deploy.sh`)

### Phase M3 — Docker 통합 배포

- Dockerfile 멀티스테이지 빌드로 개선:
  - Stage 1: Node.js → Frontend 빌드
  - Stage 2: Python → Backend + Static 서빙
- docker-compose.yml 업데이트 (필요 시)
- 컨테이너 빌드 및 실행 테스트

### Phase M4 — 최종 검증 & 문서화

- 통합 환경 E2E 스모크 테스트 (전체 파이프라인)
- `.env.example` 통합 문서화 (Backend + Frontend 환경 변수 통합)
- 완료 리포트: `report/claude_report_master_integration.md`

---

## 환경 변수 (통합)

| 변수명 | 출처 | 필수 | 기본값 |
|--------|------|------|--------|
| `GEMINI_API_KEY` | Backend | 필수 | — |
| `GEMINI_MODEL` | Backend | 선택 | `gemini-2.5-flash-lite` |
| `GMAIL_CREDENTIALS_PATH` | Backend | 필수 | `./credentials.json` |
| `DATABASE_URL` | Backend | 선택 | `sqlite:///./tldr.db` |
| `CHROMA_PERSIST_DIR` | Backend | 선택 | `./chroma_db` |
| `SYNC_SCHEDULE_HOUR` | Backend | 선택 | `7` |
| `CORS_ORIGINS` | Backend | 선택 | `http://localhost:3000` |
| `DAILY_API_CALL_LIMIT` | Backend | 선택 | `900` |
| `VITE_API_BASE_URL` | Frontend | 선택 | (빈 값 — 상대 경로) |
| `VITE_USE_MOCK` | Frontend | 선택 | `false` (프로덕션) |

---

## 완료 조건

- [ ] `GET /api/categories` 응답 정상 반환 (카테고리명 + 기사 수)
- [ ] Frontend에서 Mock 없이 Backend API 직접 연동 정상 동작
- [ ] `http://localhost:8000`에서 API + Frontend 단일 서버 서빙 확인
- [ ] Docker 빌드 및 컨테이너 실행 정상 확인
- [ ] E2E 스모크 테스트: Gmail 동기화 → AI 처리 → API 응답 → UI 렌더링
- [ ] `report/claude_report_master_integration.md` 완료 리포트 저장
