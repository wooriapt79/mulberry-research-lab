"""GitHub Issue에 동적으로 댓글을 게시합니다.

이 스크립트는 지정된 GitHub 리포지토리의 이슈에 댓글을 게시하는 데 사용됩니다.
이슈 번호와 댓글 내용을 명령줄 인자로 받습니다.

사용법:
python scripts/post_issue24_comment.py <issue_number> <comment_body>

예시:
python scripts/post_issue24_comment.py 24 "안녕하세요! 테스트 댓글입니다."
"""
import urllib.request
import urllib.error
import json
import os
import sys

# 인자 확인
if len(sys.argv) < 3:
    print("사용법: python scripts/post_issue24_comment.py <issue_number> <comment_body>")
    sys.exit(1)

issue_number = sys.argv[1]
comment_body = sys.argv[2]

token = os.environ.get("GITHUB_TOKEN", "")
if not token:
    print("GITHUB_TOKEN 없음 — Railway 환경에서 실행하거나 환경변수 설정 필요")
    sys.exit(1)

payload = json.dumps({"body": comment_body}).encode("utf-8")
req = urllib.request.Request(
    f"https://api.github.com/repos/wooriapt79/mulberry-research-lab/issues/{issue_number}/comments",
    data=payload,
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        print(f"댓글 게시 완료: {result['html_url']}")

except urllib.error.HTTPError as e:
    error_body = e.read().decode("utf-8")
    print(f"GitHub API 오류 {e.code}: {error_body}")
    if e.code == 401:
        print("GITHUB_TOKEN 권한 또는 만료 상태 확인 필요")
    elif e.code == 403:
        print("레포지토리 쓰기 권한 또는 Rate Limit 확인")
    elif e.code == 404:
        print("URL 또는 이슈 번호 확인 필요")
    elif e.code == 422:
        print("요청 본문 형식 오류 (body 키/마크다운 구문 확인)")
    sys.exit(1)

except Exception as e:
    print(f"예상치 못한 오류: {type(e).__name__}: {e}")
    sys.exit(1)
