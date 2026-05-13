"""
Mulberry GitHub 이슈 댓글 CLI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
사용법:
  python scripts/comment.py <이슈번호> "<댓글내용>" [에이전트명]

예시:
  python scripts/comment.py 24 "RyuWon 의견: LGTM 👍" RyuWon
  python scripts/comment.py 26 "Phase 2 준비 완료입니다."

환경변수 (.env.railway):
  GITHUB_TOKEN  — 필수 (GitHub Personal Access Token)

토큰 발급:
  https://github.com/settings/tokens → New token → repo 권한 체크
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

REPO = "wooriapt79/mulberry-research-lab"

# ── 환경변수 로드 (.env.railway 우선 → 시스템 환경) ──────────

def load_env():
    env_path = Path(__file__).parent.parent / ".env.railway"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

load_env()

# ── 인자 파싱 ────────────────────────────────────────────────

def usage():
    print(__doc__)
    sys.exit(1)

if len(sys.argv) < 3:
    usage()

issue_number = sys.argv[1]
body_raw     = sys.argv[2]
agent_name   = sys.argv[3] if len(sys.argv) > 3 else ""

if not issue_number.isdigit():
    print(f"❌ 이슈 번호가 숫자여야 합니다: {issue_number}")
    usage()

# ── 댓글 본문 조립 ───────────────────────────────────────────

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
agent_line = f"\n\n---\n*[{agent_name}] Mulberry Research Lab · {now}*" if agent_name else f"\n\n---\n*Mulberry Research Lab · {now}*"
body = body_raw + agent_line

# ── GitHub API 호출 ──────────────────────────────────────────

token = os.environ.get("GITHUB_TOKEN", "")
if not token:
    print("❌ GITHUB_TOKEN이 설정되지 않았습니다.")
    print("   .env.railway 파일에 GITHUB_TOKEN=your_token_here 를 입력하세요.")
    print("   토큰 발급: https://github.com/settings/tokens")
    sys.exit(1)

url  = f"https://api.github.com/repos/{REPO}/issues/{issue_number}/comments"
data = json.dumps({"body": body}).encode("utf-8")
req  = urllib.request.Request(
    url, data=data,
    headers={
        "Authorization": f"token {token}",
        "Accept":        "application/vnd.github.v3+json",
        "Content-Type":  "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        print(f"✅ 댓글 게시 완료!")
        print(f"   이슈  : #{issue_number}")
        print(f"   URL   : {result['html_url']}")
        if agent_name:
            print(f"   작성자: {agent_name}")
except urllib.error.HTTPError as e:
    code = e.code
    body_err = e.read().decode("utf-8")
    if code == 401:
        print("❌ 인증 실패 — GITHUB_TOKEN을 확인하세요.")
    elif code == 404:
        print(f"❌ 이슈 #{issue_number}를 찾을 수 없습니다.")
    elif code == 403:
        print("❌ 권한 없음 — 토큰에 'repo' 권한이 있는지 확인하세요.")
    else:
        print(f"❌ HTTP {code}: {body_err}")
    sys.exit(1)
