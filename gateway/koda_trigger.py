# gateway/koda_trigger.py
"""
Mulberry Koda Trigger — "기술은 보이지 않게, 사람이 중심, AI는 도구"

이 문구가 감지되면 Koda(Claude)를 호출하고
응답을 Relay Gateway를 통해 GitHub Issue에 자동 게시한다.

사용:
  python koda_trigger.py --issue 19 --message "질문 내용"
  또는 Socket.IO 룸 메시지로 자동 감지
"""

import os
import json
import urllib.request
import argparse

TRIGGER_PHRASE = "기술은 보이지 않게"  # 트리거 감지 키워드
GATEWAY_URL = "https://mulberry-research-lab-production.up.railway.app"
GATEWAY_SECRET = os.environ.get("GATEWAY_SECRET", "mulberry-agent-relay-2026")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def is_trigger(message: str) -> bool:
    """트리거 문구 감지"""
    return TRIGGER_PHRASE in message


def call_koda(prompt: str, context: str = "") -> str:
    """Anthropic API로 Koda 호출"""
    if not ANTHROPIC_API_KEY:
        return "[Koda] ANTHROPIC_API_KEY 미설정 — 응답 불가"

    system = (
        "당신은 Koda입니다. Mulberry 프로젝트의 Claude 에이전트입니다. "
        "장승배기 헌법 정신(기술은 보이지 않게, 사람이 중심, AI는 도구)을 따릅니다. "
        "간결하고 실용적으로 답합니다."
    )

    data = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "system": system,
        "messages": [{"role": "user", "content": f"{context}\n\n{prompt}".strip()}],
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(data).encode(),
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["content"][0]["text"]
    except Exception as e:
        return f"[Koda] API 호출 실패: {e}"


def post_to_gateway(issue_number: int, content: str, repo: str = "mulberry-research-lab") -> bool:
    """Relay Gateway를 통해 GitHub Issue에 게시"""
    data = {
        "agent_id": "koda",
        "content": content,
        "repo": repo,
        "issue_number": issue_number,
    }
    req = urllib.request.Request(
        f"{GATEWAY_URL}/post",
        data=json.dumps(data).encode(),
        headers={
            "x-gateway-secret": GATEWAY_SECRET,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[Gateway] {resp.status} — 게시 완료")
            return True
    except Exception as e:
        print(f"[Gateway] 게시 실패: {e}")
        return False


def post_direct_github(issue_number: int, content: str, repo: str = "wooriapt79/mulberry-research-lab") -> bool:
    """Gateway 우회 — GitHub API 직접 게시 (fallback)"""
    if not GITHUB_TOKEN:
        print("[GitHub] GITHUB_TOKEN 미설정")
        return False

    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    req = urllib.request.Request(
        url,
        data=json.dumps({"body": content}).encode(),
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            print(f"[GitHub] 직접 게시 완료: {result['html_url']}")
            return True
    except Exception as e:
        print(f"[GitHub] 직접 게시 실패: {e}")
        return False


def handle_trigger(message: str, issue_number: int, context: str = "") -> None:
    """트리거 감지 → Koda 호출 → 결과 게시 전체 파이프라인"""
    if not is_trigger(message):
        print(f"[Trigger] 감지 안됨: '{message[:30]}...'")
        return

    print(f"[Trigger] 감지! Issue #{issue_number} 대상으로 Koda 호출...")
    response = call_koda(message, context)

    content = f"## Koda 응답\n\n{response}\n\n---\n*Triggered by: \"{TRIGGER_PHRASE}...\" | Koda (Claude)*"

    # Gateway 시도 → 실패 시 GitHub 직접 게시
    if not post_to_gateway(issue_number, content):
        print("[Trigger] Gateway 실패 - GitHub 직접 게시로 전환")
        post_direct_github(issue_number, content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Koda Trigger")
    parser.add_argument("--issue", type=int, required=True, help="GitHub Issue 번호")
    parser.add_argument("--message", type=str, required=True, help="트리거 메시지")
    parser.add_argument("--context", type=str, default="", help="추가 컨텍스트")
    args = parser.parse_args()

    handle_trigger(args.message, args.issue, args.context)
