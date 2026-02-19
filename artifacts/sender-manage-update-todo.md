# 뉴스레터 발신자 관리 기능 — Todo List

## Backend

- [ ] **DB 스키마**: `senders` 테이블 생성 (`id`, `name`, `email`, `is_active`, `created_at`)
- [ ] **DB 마이그레이션**: 초기화 시 `.env`의 기존 발신자를 시드 데이터로 삽입
- [ ] **DB CRUD 함수**: `get_senders`, `get_active_sender_emails`, `add_sender`, `update_sender`, `delete_sender`
- [ ] **API 라우터**: `/api/senders` CRUD 엔드포인트 (GET/POST/PUT/DELETE)
- [ ] **Pydantic 모델**: `SenderCreate`, `SenderUpdate`, `SenderResponse`
- [ ] **라우터 등록**: `main.py`에 senders 라우터 include
- [ ] **Gmail 서비스 수정**: `fetch_tldr_emails()`에서 DB 기반 활성 발신자 조회로 전환

## Frontend

- [ ] **API 클라이언트**: `fetchSenders`, `addSender`, `updateSender`, `deleteSender` 함수 추가
- [ ] **Mock 데이터**: 발신자 mock 데이터 추가 (`VITE_USE_MOCK` 대응)
- [ ] **App.jsx 수정**: Settings 아이콘 버튼 + `showSettings` state + 페이지 전환 로직
- [ ] **SettingsPage 컴포넌트**: 설정 페이지 레이아웃 (헤더 + 뒤로가기 + 섹션 구성)
- [ ] **SettingsPage 스타일**: `SettingsPage.css`
- [ ] **SenderManager 컴포넌트**: 발신자 CRUD UI (목록 테이블 + 추가 폼 + 인라인 편집 + 활성/비활성 토글)
- [ ] **SenderManager 스타일**: `SenderManager.css`
- [ ] **유효성 검증**: 이메일 형식 검증, 중복 검사
- [ ] **UX**: 삭제 확인 다이얼로그, Toast 알림 연동

## 검증

- [ ] 서버 시작 시 `senders` 테이블 생성 + `.env` 발신자 자동 시드 확인
- [ ] `/api/senders` CRUD 엔드포인트 정상 동작 확인 (FastAPI `/docs`)
- [ ] 발신자 추가/비활성화 후 동기화 시 해당 발신자 이메일만 수집되는지 확인
- [ ] Settings 페이지에서 발신자 추가/수정/삭제/토글 전체 UI 흐름 확인
