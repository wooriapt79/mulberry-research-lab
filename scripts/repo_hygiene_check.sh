#!/bin/bash
# scripts/repo_hygiene_check.sh — Mulberry 레포 위생 점검 자동화
# GitHub Actions 및 로컬 모두에서 실행 가능

set -e  # 오류 발생 시 즉시 중단

echo "🧹 Mulberry 레포 위생 점검 시작..."
echo "📅 실행 시각: $(date -Iseconds)"
echo "🔖 브랜치: $(git branch --show-current)"
echo "🔖 커밋: $(git rev-parse --short HEAD)"
echo ""

# 1️⃣ 임시/백업 파일 탐색 (삭제 전 확인용)
echo "📋 [1] 임시/백업 파일 후보:"
TEMP_FILES=$(find . -type f \( -name "*_v[0-9]*.py" -o -name "*_backup.py" -o -name "*_final.py" -o -name "*.py.bak" -o -name "~*.py" \) 2>/dev/null || true)
if [ -z "$TEMP_FILES" ]; then
  echo "✅ 발견되지 않음"
else
  echo "$TEMP_FILES"
fi
echo ""

# 2️⃣ 하드코딩 시크릿 탐색 (간이 패턴)
echo "🔍 [2] 하드코딩 시크릿 후보:"
SECRET_PATTERNS=$(grep -rn "ghp_[a-zA-Z0-9]\{20,\}\|sk-[a-zA-Z0-9]\{20,\}\|Bearer [a-zA-Z0-9._-]\{20,\}" --include="*.py" --exclude-dir=.git --exclude-dir=node_modules . 2>/dev/null || true)
if [ -z "$SECRET_PATTERNS" ]; then
  echo "✅ 발견되지 않음"
else
  echo "⚠️ 주의: 아래 패턴을 확인해 주세요"
  echo "$SECRET_PATTERNS"
fi
echo ""

# 3️⃣ .gitignore 누락 파일 확인
echo "📁 [3] .gitignore 누락 후보:"
IGNORED_CANDIDATES=$(git status --porcelain 2>/dev/null | grep "^??" | grep -E "\.env$|\.log$|venv/|__pycache__/|\.DS_Store" || true)
if [ -z "$IGNORED_CANDIDATES" ]; then
  echo "✅ 누락 없음"
else
  echo "⚠️ 아래 파일을 .gitignore 에 추가 권장:"
  echo "$IGNORED_CANDIDATES"
fi
echo ""

# 4️⃣ 의존성 일치성 확인 (선택)
echo "📦 [4] 의존성 일치성:"
if [ -f "requirements.txt" ]; then
  pip freeze > /tmp/current.txt 2>/dev/null || true
  if diff -q /tmp/current.txt requirements.txt >/dev/null 2>&1; then
    echo "✅ requirements.txt 와 일치"
  else
    echo "⚠️ 불일치 발견 — 'pip freeze > requirements.txt' 로 동기화 권장"
    echo "📊 차이 미리보기:"
    diff /tmp/current.txt requirements.txt | head -20 || true
  fi
  rm -f /tmp/current.txt
else
  echo "⚠️ requirements.txt 없음 — 생성 권장"
fi
echo ""

# 5️⃣ 구조 명료성 체크 (간이)
echo "🗂️ [5] 구조 명료성:"
if [ -d "api/" ] && [ -d "services/" ] && [ -d "configs/" ]; then
  echo "✅ 표준 폴더 구조 (api/, services/, configs/) 존재"
else
  echo "⚠️ 표준 구조와 다를 수 있음 — README.md 와 비교 권장"
fi
echo ""

echo "✅ 위생 점검 완료."
echo "💡 결과 해석:"
echo "   • '✅' 만 보이면 현재 상태 양호"
echo "   • '⚠️' 는 개선 권장 사항 (즉시 수정 불필요)"
echo "   • '❌' 는 치명적 위험 (즉시 조치 필요)"
