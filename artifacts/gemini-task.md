# TLDR AI Newsletter Manager — 프론트엔드 구현 태스크

## Phase 0: 구현계획 수립
- [x] PRD 문서 분석 (Master, Frontend, Backend)
- [x] 프로젝트 구조 파악
- [x] 구현계획 문서 작성 및 사용자 승인

## Phase 1: 프로젝트 기반 설정
- [x] `vite.config.js` 프록시 설정 (API → localhost:8000)
- [x] `.env.development` / `.env.production` 환경변수 파일
- [x] 글로벌 CSS 디자인 시스템 (색상, 타이포, 레이아웃 변수)
- [x] `index.html` SEO 메타태그 업데이트

## Phase 3: 핵심 컴포넌트 구현
- [x] `App.jsx` — 전체 레이아웃 (네비게이션바 + 사이드바 + 메인)
- [x] `SearchBar.jsx` — 시맨틱 검색 (debounce 300ms)
- [x] `SyncStatus.jsx` — 동기화 상태/버튼
- [x] `CategoryFilter.jsx` — 사이드바 카테고리 필터 (복수 선택)
- [x] `NewsletterCalendar.jsx` — 캘린더 (복수 날짜 선택)
- [x] `ArticleCard.jsx` — 기사 카드 (카테고리 배지, 중요도, 태그 칩 등)
- [x] `ArticleList.jsx` — 카드 그리드 + 로딩 스켈레톤 + 페이지네이션
- [x] `ChatPanel.jsx` — RAG 채팅 (Phase 4, 선택)
- [x] `ArticleDetail.jsx` — 기사 상세 보기

## Phase 4: 통합 및 세부 조정
- [x] 다크/라이트 모드 토글
- [x] 에러 처리 (Toast 알림, 재시도)
- [x] 브라우저 호환성 CSS 수정
- [x] 한국어/영문 요약 토글

## Phase 5: 검증
- [x] 개발 서버 실행 및 빌드 확인
- [x] 브라우저 UI 검증 (Mock 데이터 기반)
