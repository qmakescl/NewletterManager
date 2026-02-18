# TLDR AI Newsletter Manager — 프론트엔드 구현계획

> PRD v1.3 (Frontend Antigravity) 기반 | React + Vite

## 현재 상태 분석
- **프레임워크:** Vite + React 19 초기 스캐폴딩 완료
- **설치된 의존성:** `react`, `react-dom`, `date-fns`, `react-icons`, `prop-types`
- **현재 코드:** `main.jsx`만 존재, 컴포넌트/API/스타일 코드 미구현
- **Backend:** 아직 미구현 (Claude Code 담당), 따라서 **Mock 데이터로 UI 먼저 개발**

## User Review Required

> [!IMPORTANT]
> **Backend 미구현 상태에서의 개발 전략**
> Backend API가 아직 없으므로, 프론트엔드 내부에 Mock 데이터 모듈(`src/api/mockData.js`)을 만들어 UI 개발을 진행합니다. API 클라이언트(`src/api/client.js`)는 개발 환경에서 Mock 데이터를 반환하고, 추후 Backend 완성 시 실제 API로 전환하는 구조입니다.

> [!IMPORTANT]
> **ChatPanel (Phase 4) 구현 범위**
> PRD에서 Phase 4로 분류된 ChatPanel은 이번 구현에서 **UI 껍데기만 구현**하고, 실제 RAG 기능은 Backend 연동 시 활성화합니다. 포함/제외 여부를 결정해 주세요.

---

## Proposed Changes

### 1. 프로젝트 기반 설정

#### [MODIFY] [vite.config.js](file:///Users/yoonani/Works/NewletterManager/frontend/vite.config.js)
- API 프록시 설정 추가 (`/api` → `http://localhost:8000`)
- 개발 서버 포트 3000 고정

#### [NEW] [.env.development](file:///Users/yoonani/Works/NewletterManager/frontend/.env.development)
- `VITE_API_BASE_URL=http://localhost:8000`
- `VITE_USE_MOCK=true` (Mock 데이터 사용 플래그)

#### [NEW] [.env.production](file:///Users/yoonani/Works/NewletterManager/frontend/.env.production)
- `VITE_API_BASE_URL=` (상대 경로, FastAPI 통합 서빙)
- `VITE_USE_MOCK=false`

#### [MODIFY] [index.html](file:///Users/yoonani/Works/NewletterManager/frontend/index.html)
- `<title>` 변경: "TLDR AI Newsletter Archive"
- SEO 메타태그 추가 (description, viewport 등)
- Google Fonts 링크 (Inter 폰트)

---

### 2. 디자인 시스템 (CSS)

#### [NEW] [index.css](file:///Users/yoonani/Works/NewletterManager/frontend/src/index.css)
글로벌 CSS 변수 및 리셋 스타일:
- **색상 체계:** 다크/라이트 모드 CSS 변수
  - 카테고리 색상: LLM(파란), Vision(보라), Agent(초록), Tools(빨강), Policy(주황), Research(청록)
  - 배경/텍스트/보더 색상 변수
- **타이포그래피:** Inter 폰트, 크기 체계 (xs~2xl)
- **레이아웃:** 사이드바 폭(280px), 카드 그리드 간격
- **애니메이션:** 부드러운 전환, 호버 효과, 스केल레톤 로딩

#### [NEW] [App.css](file:///Users/yoonani/Works/NewletterManager/frontend/src/App.css)
- 전체 레이아웃 (3열 그리드: 사이드바 / 메인 / 디테일패널)
- 네비게이션 바 스타일
- 반응형 기본 (1280px+ 기준)

#### [NEW] 각 컴포넌트별 CSS 모듈 파일
- `ArticleCard.css`, `ArticleList.css`, `SearchBar.css`, `CategoryFilter.css`, `NewsletterCalendar.css`, `SyncStatus.css`, `ChatPanel.css`

---

### 3. API 클라이언트

#### [NEW] [mockData.js](file:///Users/yoonani/Works/NewletterManager/frontend/src/api/mockData.js)
Backend 미구현 상태에서 UI 개발용 Mock 데이터:
- 뉴스레터 샘플 목록 (3~4일분)
- 기사 샘플 20~30개 (다양한 카테고리/중요도/태그)
- 카테고리 목록 + 기사 수

#### [NEW] [client.js](file:///Users/yoonani/Works/NewletterManager/frontend/src/api/client.js)
API 호출 함수 모음:
- `fetchArticles(params)` — 기사 목록 (dates, category, page, size)
- `fetchArticleDetail(id)` — 기사 상세
- `searchArticles(query)` — 시맨틱 검색
- `fetchCategories()` — 카테고리 목록
- `fetchNewsletters()` — 뉴스레터 날짜 목록
- `triggerSync()` — 수동 동기화
- `sendChatMessage(message)` — RAG 채팅
- `VITE_USE_MOCK=true`일 때 Mock 데이터 반환 로직

---

### 4. 핵심 컴포넌트

#### [MODIFY] [App.jsx](file:///Users/yoonani/Works/NewletterManager/frontend/src/App.jsx)
전체 레이아웃 컴포넌트:

```
┌─────────────────────────────────────────────────────┐
│  🔍 TLDR AI Archive    [SearchBar]     [SyncStatus] │
├──────────────┬──────────────────────────────────────┤
│ CategoryFilter│                                      │
│              │   ArticleList (카드 그리드)           │
│──────────────│                                      │
│ Newsletter   │                                      │
│ Calendar     ├──────────────────────────────────────┤
│              │  ArticleDetail / ChatPanel           │
└──────────────┴──────────────────────────────────────┘
```

- 상태 관리: `useState`로 필터 상태(선택 카테고리, 선택 날짜, 검색어) 관리
- URL 파라미터 동기화 (`?dates=...&category=...`)
- 다크/라이트 모드 토글 버튼

#### [NEW] [ArticleCard.jsx](file:///Users/yoonani/Works/NewletterManager/frontend/src/components/ArticleCard.jsx)
- 카테고리 색상 배지
- 중요도 별(★) 표시 (1~5)
- 영문 제목 + 한국어 요약
- 태그 칩 (클릭 시 필터 적용)
- 원문 링크 버튼 (새 탭)
- 발행일 표시
- 카드 호버 애니메이션 (미세 상승 + 그림자)

#### [NEW] [ArticleList.jsx](file:///Users/yoonani/Works/NewletterManager/frontend/src/components/ArticleList.jsx)
- 반응형 카드 그리드 (auto-fill, minmax 320px)
- API 연동: 필터 변경 시 `fetchArticles()` 호출
- 로딩 중 스켈레톤 카드 UI
- 빈 결과 시 안내 메시지
- 페이지네이션 (12개씩)

#### [NEW] [SearchBar.jsx](file:///Users/yoonani/Works/NewletterManager/frontend/src/components/SearchBar.jsx)
- 입력 debounce 300ms
- 검색 아이콘 + 입력 클리어 버튼
- `searchArticles(query)` API 호출
- 결과 키워드 하이라이트 기능

#### [NEW] [CategoryFilter.jsx](file:///Users/yoonani/Works/NewletterManager/frontend/src/components/CategoryFilter.jsx)
- `fetchCategories()`로 카테고리 목록 + 기사 수 표시
- 복수 선택 가능 (체크박스 스타일)
- 카테고리별 색상 인디케이터
- "전체" 옵션

#### [NEW] [NewsletterCalendar.jsx](file:///Users/yoonani/Works/NewletterManager/frontend/src/components/NewsletterCalendar.jsx)
`date-fns` 활용 월간 캘린더:
- 뉴스레터 수신 날짜만 클릭 가능 (나머지 비활성)
- 복수 날짜 토글 선택/해제
- 선택된 날짜 배경색 강조 + 하단 칩 표시
- 기사 합계 실시간 카운트
- 이전/다음 월 이동
- 선택 초기화 버튼
- 기본: 최신 수신일 1개 자동 선택

#### [NEW] [SyncStatus.jsx](file:///Users/yoonani/Works/NewletterManager/frontend/src/components/SyncStatus.jsx)
- 마지막 동기화 시각 표시
- 수동 동기화 버튼 + 스피너
- 완료/에러 Toast 알림

#### [NEW] [ChatPanel.jsx](file:///Users/yoonani/Works/NewletterManager/frontend/src/components/ChatPanel.jsx) *(Phase 4, 선택)*
- 채팅 UI 껍데기 (메시지 리스트 + 입력창)
- 출처 기사 카드 링크 표시 영역
- Mock 응답 또는 Backend 연동

---

### 5. 공통 유틸리티

#### [NEW] [Toast.jsx](file:///Users/yoonani/Works/NewletterManager/frontend/src/components/ui/Toast.jsx)
- 성공/에러/정보 Toast 알림 컴포넌트
- 자동 소멸 (3초)

#### [NEW] [SkeletonCard.jsx](file:///Users/yoonani/Works/NewletterManager/frontend/src/components/ui/SkeletonCard.jsx)
- 로딩 중 스켈레톤 카드 (펄스 애니메이션)

---

## 파일 구조 최종

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.js          # API 호출 함수 (Mock/실제 전환)
│   │   └── mockData.js        # 개발용 Mock 데이터
│   ├── components/
│   │   ├── ArticleCard.jsx    # 기사 카드
│   │   ├── ArticleCard.css
│   │   ├── ArticleList.jsx    # 카드 그리드 + 페이지네이션
│   │   ├── ArticleList.css
│   │   ├── SearchBar.jsx      # 검색창
│   │   ├── SearchBar.css
│   │   ├── CategoryFilter.jsx # 카테고리 필터
│   │   ├── CategoryFilter.css
│   │   ├── NewsletterCalendar.jsx  # 캘린더
│   │   ├── NewsletterCalendar.css
│   │   ├── ChatPanel.jsx      # RAG 채팅 (Phase 4)
│   │   ├── ChatPanel.css
│   │   ├── SyncStatus.jsx     # 동기화 상태
│   │   ├── SyncStatus.css
│   │   └── ui/
│   │       ├── Toast.jsx      # Toast 알림
│   │       ├── Toast.css
│   │       ├── SkeletonCard.jsx  # 스켈레톤 로딩
│   │       └── SkeletonCard.css
│   ├── App.jsx                # 메인 레이아웃
│   ├── App.css
│   ├── index.css              # 글로벌 디자인 시스템
│   └── main.jsx               # 엔트리 포인트
├── .env.development
├── .env.production
├── index.html
├── vite.config.js
└── package.json
```

**총 신규 파일: 약 22개** (JSX 10개, CSS 10개, 환경변수 2개)
**수정 파일: 3개** (`vite.config.js`, `index.html`, `App.jsx`)

---

## Verification Plan

### 개발 서버 실행 확인
```bash
cd /Users/yoonani/Works/NewletterManager/frontend
npm run dev
```
- 포트 3000에서 정상 기동 확인
- 브라우저에서 http://localhost:3000 접속 후 레이아웃 확인

### 빌드 검증
```bash
cd /Users/yoonani/Works/NewletterManager/frontend
npm run build
```
- `dist/` 폴더 정상 생성 확인
- 빌드 에러 없음 검증

### 브라우저 UI 검증
Mock 데이터 기반으로 다음 항목을 브라우저에서 확인:
1. 전체 레이아웃 (네비게이션바 + 사이드바 + 메인 그리드) 렌더링
2. ArticleCard 카테고리 색상, 별점, 태그 표시
3. CategoryFilter 복수 선택 → 기사 목록 필터링
4. NewsletterCalendar 날짜 선택 → 기사 목록 변경
5. SearchBar 입력 → 검색 결과 표시
6. 다크/라이트 모드 토글
7. 페이지네이션 동작

### 수동 검증 (사용자)
- 디자인 퀄리티 및 UX 만족도 확인
- Backend 연동 시 API 전환 테스트 (`.env` 수정으로 Mock ↔ 실제 전환)
