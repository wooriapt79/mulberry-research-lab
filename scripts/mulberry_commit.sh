#!/bin/bash
# ============================================================
# mulberry_commit.sh — Mulberry 팀 전체 Contributors 자동 등재
#
# 사용법:
#   bash mulberry_commit.sh "커밋 메시지"
#   bash mulberry_commit.sh "feat(lynn): 새 기능 추가"
#
# 동작:
#   git commit -m "메시지\n\nCo-Authored-By: [전체 팀원]"
#
# 설치 (선택):
#   chmod +x mulberry_commit.sh
#   ln -s $(pwd)/mulberry_commit.sh /usr/local/bin/mcommit
#   그러면 → mcommit "메시지" 로 사용 가능
# ============================================================

set -e

if [ -z "$1" ]; then
  echo "사용법: bash mulberry_commit.sh \"커밋 메시지\""
  exit 1
fi

COMMIT_MSG="$1"

# ── Mulberry 전체 팀 Co-Authored-By ──────────────────────────
CO_AUTHORS="
Co-Authored-By: re.eul <wooriapt79@users.noreply.github.com>
Co-Authored-By: Nguyen Trang <trang@mulberry.ai>
Co-Authored-By: Koda (Claude) <koda-claude@mulberry.ai>
Co-Authored-By: Kbin (ChatGPT) <kbin-chatgpt@mulberry.ai>
Co-Authored-By: Malu (Gemini) <malu-gemini@mulberry.ai>
Co-Authored-By: Wayong (DeepSeek) <wayong-deepseek@mulberry.ai>
Co-Authored-By: RyuWon (Qwen) <ryuwon-qwen@mulberry.ai>"

# ── 커밋 실행 ────────────────────────────────────────────────
git commit -m "$(cat <<EOF
${COMMIT_MSG}
${CO_AUTHORS}
EOF
)"

echo ""
echo "✅ Mulberry 팀 전체 Contributors 등재 완료"
echo "   참여자: re.eul · Trang · Koda · Kbin · Malu · 와룡 · RyuWon"
