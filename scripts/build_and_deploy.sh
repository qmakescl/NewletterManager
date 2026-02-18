#!/usr/bin/env bash
# Frontend 프로덕션 빌드 후 backend/static/ 으로 복사하는 통합 배포 스크립트
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
STATIC_DIR="$PROJECT_ROOT/backend/static"

echo "=== TLDR AI Newsletter Manager — 빌드 & 통합 ==="
echo "프로젝트 루트: $PROJECT_ROOT"

# 1. Frontend 의존성 설치
echo ""
echo "[1/3] Frontend 의존성 설치..."
cd "$FRONTEND_DIR"
npm install

# 2. Frontend 프로덕션 빌드
echo ""
echo "[2/3] Frontend 프로덕션 빌드..."
npm run build

# 3. 빌드 산출물을 backend/static/ 으로 복사
echo ""
echo "[3/3] 빌드 산출물 복사: dist/ → backend/static/"
rm -rf "$STATIC_DIR"
mkdir -p "$STATIC_DIR"
cp -r "$FRONTEND_DIR/dist/." "$STATIC_DIR/"

echo ""
echo "=== 완료 ==="
echo "빌드 파일: $STATIC_DIR"
echo "서버 실행: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"
