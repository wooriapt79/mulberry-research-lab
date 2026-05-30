#!/usr/bin/env python3
"""
koda_post_comment.py — Koda CTO GitHub 댓글 직접 게시
=====================================================
사용법:
  python scripts/koda_post_comment.py {이슈번호} {댓글내용파일.md}
  python scripts/koda_post_comment.py 81 comment.md

환경변수 (.env.local):
  GITHUB_TOKEN — Railway loving-education 서비스에서 복사

작성: Koda CTO · 2026-05-31
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# .env.local 로드
env_file = Path(__file__).parent.parent / ".env.local"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

REPO       = "wooriapt79/mulberry-research-lab"
GH_TOKEN   = os.getenv("GITHUB_TOKEN", "")


def post_comment(issue_number: str, body: str) -> bool:
    if not GH_TOKEN or GH_TOKEN == "your_github_pat_here":
        print("❌ GITHUB_TOKEN 미설정 — .env.local 확인")
        return False

    url = f"https://api.github.com/repos/{REPO}/issues/{issue_number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 201:
                print(f"✅ Issue #{issue_number} 댓글 게시 완료")
                return True
    except Exception as e:
        print(f"❌ 게시 실패: {e}")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("사용법: python koda_post_comment.py {이슈번호} {댓글파일.md}")
        sys.exit(1)

    issue_num  = sys.argv[1]
    comment_md = Path(sys.argv[2])

    if not comment_md.exists():
        print(f"❌ 파일 없음: {comment_md}")
        sys.exit(1)

    body = comment_md.read_text(encoding="utf-8")
    post_comment(issue_num, body)
