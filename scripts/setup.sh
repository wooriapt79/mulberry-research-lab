#!/usr/bin/env bash
# ============================================================
# Mulberry Research Lab — 로컬 환경 셋업 스크립트
# 작성: RyuWon 초안 → Koda 보완 (2026-05-12)
#
# 사용법:
#   bash scripts/setup.sh
# ============================================================

set -e  # 오류 발생 시 중단

PROJECT_DIR="$HOME/projects/mulberry-research-lab"
REPO_URL="https://github.com/wooriapt79/mulberry-research-lab.git"

echo "======================================================"
echo "  Mulberry Research Lab — 환경 셋업"
echo "======================================================"

# 1. 프로젝트 폴더 확인 (없으면 클론)
if [ ! -d "$PROJECT_DIR" ]; then
    echo "🔄 레포지토리 클론 중..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    echo "✅ 클론 완료: $PROJECT_DIR"
else
    echo "✅ 프로젝트 폴더 이미 존재: $PROJECT_DIR"
    cd "$PROJECT_DIR" && git pull origin main --quiet
    echo "✅ 최신 코드 pull 완료"
fi

# 2. 프로젝트 폴더로 이동
cd "$PROJECT_DIR"

# 3. Python 버전 확인
PYTHON_VERSION=$(python3 --version 2>&1)
echo "✅ $PYTHON_VERSION"

# 4. 가상환경 확인 (없으면 생성)
if [ ! -d "venv" ]; then
    echo "🔄 가상환경 생성 중..."
    python3 -m venv venv
    echo "✅ venv 생성 완료"
else
    echo "✅ venv 이미 존재"
fi

# 5. 가상환경 활성화
source venv/bin/activate
echo "✅ 가상환경 활성화됨: $(which python)"

# 6. 의존성 설치
echo "🔄 의존성 확인 중..."
pip install --quiet pyyaml requests
python -c "import yaml; print('✅ yaml OK')"

# 7. .env.railway 확인 (없으면 템플릿 복사)
if [ ! -f ".env.railway" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env.railway
        echo ""
        echo "🟡 .env.railway 생성됨 — 반드시 토큰 값을 입력하세요!"
        echo "   nano .env.railway"
        echo "   → GITHUB_TOKEN=ghp_xxxxxxx  (필수)"
        echo "   → RAILWAY_API_TOKEN=...      (AI-SIEM Phase 2용)"
        echo ""
    else
        echo "⚠️  .env.example 파일이 없습니다. 최신 코드를 pull 해주세요."
    fi
else
    echo "✅ .env.railway 이미 존재"
fi

# 8. GITHUB_TOKEN 확인
if grep -q "your_github_token_here" .env.railway 2>/dev/null; then
    echo ""
    echo "⚠️  GITHUB_TOKEN이 아직 기본값입니다."
    echo "   토큰 발급: https://github.com/settings/tokens"
    echo "   → New token (classic) → repo 권한 체크 → 생성"
    echo "   → nano .env.railway 에서 GITHUB_TOKEN= 값 교체"
else
    # 환경변수 로드 후 확인
    export $(grep -v '^#' .env.railway | xargs) 2>/dev/null || true
    if [ -n "$GITHUB_TOKEN" ]; then
        echo "✅ GITHUB_TOKEN 설정됨"
    fi
fi

echo ""
echo "======================================================"
echo "  셋업 완료! 다음 명령어를 사용할 수 있습니다:"
echo ""
echo "  # 이슈에 댓글 달기"
echo "  python scripts/comment.py <이슈번호> \"<댓글내용>\" <에이전트명>"
echo ""
echo "  예시:"
echo "  python scripts/comment.py 26 \"RyuWon 의견: LGTM 👍\" RyuWon"
echo "  python scripts/comment.py 24 \"추가 검토 요청합니다.\" RyuWon"
echo "======================================================"
