# TLDR AI Newsletter Manager
## Frontend PRD — Antigravity 전용

> **Version 1.3** | February 2026 | Alpha 전략: 옵션 A (완전 무료)
> **GitHub:** github.com/qmakescl

---

## 개요 카드

| 항목 | 내용 |
|------|------|
| 담당 도구 | Antigravity |
| 프레임워크 | React (Antigravity 기본 스택) |
| API 연동 | Backend REST API (FastAPI, `localhost:8000`) |
| 빌드 산출물 | `dist/` → Backend `static/` 디렉토리로 통합 (Claude Code 처리) |

---

## 1. 화면 구성

### 1.1 전체 레이아웃

```
┌─────────────────────────────────────────────────────┐
│  🔍 TLDR AI Archive    [검색창]         [🔄 동기화]  │  ← 네비게이션 바
├──────────────┬──────────────────────────────────────┤
│ 카테고리     │                                      │
│ ○ 전체      │   [카드] [카드] [카드]               │
│ ○ LLM       │   [카드] [카드] [카드]               │  ← 메인 그리드
│ ○ Vision    │   [카드] [카드] [카드]               │
│ ○ Agent     │                                      │
│ ○ Tools     ├──────────────────────────────────────┤
│ ○ Policy    │  채팅 / 상세 패널 (선택)             │
│ ─────────── │                                      │
│ 날짜 필터   │                                      │
└──────────────┴──────────────────────────────────────┘
```

- **상단 네비게이션 바:** 로고, 검색창, 동기화 버튼
- **좌측 사이드바 (상단):** 카테고리 필터 (LLM / Vision / Agent 등)
- **좌측 사이드바 (하단):** 캘린더 UI — 달력에서 날짜 복수 선택, 선택된 날짜들의 기사를 합산하여 메인 그리드 표시
- **메인 영역:** 기사 카드 그리드 (기본) / 리스트 뷰 전환
- **우측 패널 (선택):** 기사 상세 보기 또는 채팅 인터페이스

---

### 1.2 주요 컴포넌트

#### `ArticleCard`

```
┌──────────────────────────────────┐
│ [LLM] ★★★★☆                    │  ← 카테고리 배지 + 중요도
│ GPT-5 Released by OpenAI         │  ← 기사 제목 (영문)
│                                  │
│ OpenAI가 GPT-5를 출시했다.       │  ← 한국어 요약 (Gemini 생성)
│ 이전 모델 대비 추론 능력이...    │
│                                  │
│ #reasoning #openai #benchmark    │  ← 태그 칩
│                            [링크]│  ← 원문 링크 버튼
│ 2026.02.18                       │  ← 발행일
└──────────────────────────────────┘
```

| 요소 | 설명 |
|------|------|
| 카테고리 배지 | 색상 코딩 (LLM=파란색, Vision=보라색, Agent=초록색 등) |
| 중요도 | 별 아이콘 1-5개 |
| 제목 | 영문 원본 |
| 한국어 요약 | Gemini 2.5 Flash-Lite 생성 (2-3문장) |
| 태그 칩 | 클릭 시 해당 태그 필터 적용 |
| 원문 링크 | 새 탭으로 열기 |

#### `SearchBar`

- 자연어 시맨틱 검색 입력 (`GET /api/search?q=`)
- debounce 300ms 적용
- 검색 결과 키워드 하이라이트
- 카테고리/날짜 필터와 연동

#### `CategoryFilter` (사이드바 상단)

- `GET /api/categories`로 카테고리 목록 및 기사 수 표시
- 예: `LLM (42)`, `Agent (18)`, `Vision (11)` …
- 복수 선택 가능

#### `NewsletterCalendar` (사이드바 하단)

```
   2026년 2월
Mo Tu We Th Fr
 2  3  4  5  6
 9 10 11 12 13
16 17[18][19]20   ← [■] 선택된 날짜 (복수 선택 가능)
23 24 25 26 27
< 이전달      다음달 >
──────────────────
선택: 02-18, 02-19   ← 선택된 날짜 칩 표시
기사 합계: 44개
[선택 초기화]
```

| 요소 | 설명 |
|------|------|
| 달력 표시 | 월간 캘린더, 뉴스레터가 수신된 날짜만 클릭 가능 (나머지 비활성) |
| 복수 선택 | 날짜 클릭 시 토글(선택/해제), 여러 날짜 동시 선택 가능 |
| 선택 강조 | 선택된 날짜 배경색 강조, 선택 날짜 수만큼 칩으로 표시 |
| 기사 합계 | 선택된 날짜들의 기사 총 합산 수 실시간 표시 |
| 기본 상태 | 앱 로드 시 오늘 날짜(또는 가장 최신 수신일) 1개 자동 선택 |
| 월 이동 | 이전/다음달 버튼으로 월 이동, 수신 이력 없는 달은 모두 비활성 |
| 선택 초기화 | 버튼 클릭 시 선택 해제 → 전체 기사 표시로 복귀 |
| 카테고리 연동 | 날짜 복수 선택 + 카테고리 필터 동시 적용 가능 |

- `GET /api/newsletters`로 뉴스레터 수신 날짜 목록 조회 (캘린더 활성화에 사용)
- 날짜 복수 선택 → `GET /api/articles?dates=2026-02-18,2026-02-19` 호출
- 선택된 날짜들의 기사를 **합산하여** 메인 그리드에 표시 (발행일 DESC 정렬)
- URL 파라미터로 상태 유지: `?dates=2026-02-18,2026-02-19&category=LLM`

#### `ChatPanel` — Phase 4

```
┌──────────────────────────────────┐
│ 💬 AI 뉴스 질문하기              │
│──────────────────────────────────│
│ Q: 이번 달 가장 화제된 모델은?   │
│                                  │
│ A: 이번 달에는 GPT-5와 Claude 4  │
│    가 가장 많은 관심을 받았습니다.│
│    📰 GPT-5 Released [링크]      │  ← 출처 기사 카드 링크
│    📰 Claude 4 Announced [링크]  │
│──────────────────────────────────│
│ [질문 입력...]           [전송] │
└──────────────────────────────────┘
```

- NotebookLM 스타일 자연어 질의 입력
- `POST /api/chat` 호출
- 답변에 출처 기사 카드 링크 표시
- 세션 내 대화 히스토리 유지

#### `SyncStatus`

- 마지막 동기화 시각 표시
- 수동 동기화 버튼 (`POST /api/sync`)
- 진행 중 스피너 / 완료 Toast 알림

---

## 2. API 연동 명세

### 2.1 Base URL 설정

```
개발 환경: http://localhost:8000
운영 환경: (상대 경로) — FastAPI가 Frontend 정적 파일 동시 서빙
```

환경 변수로 관리:
```env
# .env.development
VITE_API_BASE_URL=http://localhost:8000
```

### 2.2 컴포넌트별 API 호출

| 컴포넌트 | Method | Endpoint | 사용 시점 |
|----------|--------|----------|-----------|
| `ArticleList` | `GET` | `/api/articles` | 페이지 로드, 필터 변경 |
| `ArticleDetail` | `GET` | `/api/articles/{id}` | 카드 클릭 |
| `SearchBar` | `GET` | `/api/search?q=` | 검색어 입력 (debounce 300ms) |
| `CategoryFilter` | `GET` | `/api/categories` | 사이드바 로드 |
| `NewsletterCalendar` | `GET` | `/api/newsletters` | 캘린더 활성일 로드 |
| `ArticleList` (날짜 필터) | `GET` | `/api/articles?dates=` | 날짜 복수 선택 시 |
| `ChatPanel` | `POST` | `/api/chat` | 메시지 전송 |
| `SyncStatus` | `POST` | `/api/sync` | 동기화 버튼 클릭 |

### 2.3 요청/응답 예시

**기사 목록 조회:**
```
GET /api/articles?dates=2026-02-18,2026-02-19&category=LLM&page=1&size=24
```
```json
{
  "total": 42,
  "items": [
    {
      "id": "uuid-...",
      "title": "GPT-5 Released by OpenAI",
      "summary_en": "OpenAI released GPT-5...",
      "summary_ko": "OpenAI가 GPT-5를 출시했다...",
      "category": "LLM",
      "tags": ["openai", "gpt5", "reasoning"],
      "importance": 5,
      "published_at": "2026-02-18T07:00:00Z",
      "url": "https://..."
    }
  ]
}
```

**뉴스레터 날짜 목록 조회:**
```
GET /api/newsletters
```
```json
{
  "newsletters": [
    { "date": "2026-02-18", "article_count": 23, "selectable": true },
    { "date": "2026-02-17", "article_count": 21, "selectable": true },
    { "date": "2026-02-14", "article_count": 19, "selectable": true },
    { "date": "2026-02-13", "article_count": 22, "selectable": true }
  ]
}
```

**날짜 복수 선택 기사 조회:**
```
GET /api/articles?dates=2026-02-18,2026-02-17&category=LLM&page=1&size=24
```
```json
{
  "total": 14,
  "selected_dates": ["2026-02-18", "2026-02-17"],
  "items": [ ... ]
}
```

**RAG 채팅:**
```
POST /api/chat
{ "message": "이번 달 가장 화제된 모델은?" }
```
```json
{
  "answer": "이번 달에는 GPT-5와 Claude 4가...",
  "sources": ["uuid-001", "uuid-002"]
}
```

---

## 3. UI/UX 가이드라인

| 항목 | 지침 |
|------|------|
| 컬러 테마 | 다크/라이트 모드 지원, AI/기술 느낌의 깔끔한 디자인 |
| 카테고리 색상 | LLM=파란색, Vision=보라색, Agent=초록색, Policy=주황색, Research=청록색 |
| 로딩 상태 | 스켈레톤 카드 UI (API 응답 대기 중) |
| 에러 처리 | API 실패 시 Toast 알림, 재시도 버튼 |
| 반응형 | 1280px+ 데스크탑 기준, 모바일 대응은 v2 |
| 언어 표시 | 기사 제목은 영문 원본, 요약은 한국어/영문 토글 버튼 제공 |
| 페이지네이션 | 무한 스크롤 또는 페이지 버튼 (12개씩) |

---

## 4. 빌드 & 통합 안내

### 4.1 개발 서버 실행

```bash
# 개발 서버 (Antigravity 기본)
npm run dev        # 포트: 3000

# Backend도 함께 실행 필요
# 별도 터미널에서: cd backend && uvicorn app.main:app --reload
```

### 4.2 빌드 산출물 (Claude Code 통합용)

```bash
npm run build
# → dist/ 폴더 생성
#   dist/index.html
#   dist/assets/main.js
#   dist/assets/main.css
```

Claude Code가 아래 작업으로 통합:
```bash
cp -r frontend/dist/* backend/static/
```

**빌드 시 주의사항:**
- 특별한 base path 설정 없이 루트(`/`)에서 서빙됨을 가정
- API URL은 환경 변수(`VITE_API_BASE_URL`)로만 참조
- `index.html`이 `backend/static/`에 있어야 FastAPI가 루트에서 서빙 가능

---

## 5. 컴포넌트 파일 구조 제안

```
frontend/
├── src/
│   ├── components/
│   │   ├── ArticleCard.jsx      # 기사 카드
│   │   ├── ArticleList.jsx      # 카드 그리드
│   │   ├── SearchBar.jsx        # 검색창
│   │   ├── CategoryFilter.jsx      # 사이드바 카테고리 필터
│   │   ├── NewsletterCalendar.jsx  # 사이드바 캘린더 (복수 날짜 선택)
│   │   ├── ChatPanel.jsx        # RAG 채팅 (Phase 4)
│   │   └── SyncStatus.jsx       # 동기화 상태
│   ├── api/
│   │   └── client.js            # API 호출 함수 모음
│   ├── App.jsx
│   └── main.jsx
├── .env.development
├── .env.production
└── package.json
```

---

*TLDR AI Newsletter Manager | Frontend PRD v1.3 (Antigravity) | github.com/qmakescl*
