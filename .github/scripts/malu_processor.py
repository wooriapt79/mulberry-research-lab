#!/usr/bin/env python3
"""
malu_processor.py — Malu Agent Brain (Gemini-powered)
GitHub Actions 트리거: 이슈 코멘트에 @Malu-Agent 언급 시 자동 실행
환경변수: GEMINI_API_KEY, MALU_TOKEN
Mulberry Research Lab · v1.1
"""

import json
import os
import time
import urllib.request
import urllib.error


# ── Mulberry 페르소나 프롬프트 ────────────────────────────────────

MALU_SYSTEM = """
당신은 Malu(말루)입니다 — Mulberry Research Lab의 법률·마케팅 담당 에이전트입니다.
이모지: 🌺  |  역할: 법률 검토, 마케팅 전략, 외부 커뮤니케이션

응답 원칙:
- 따뜻하고 전문적인 어조 유지
- Mulberry Research Lab의 '장승배기 헌법 정신' 기반으로 응답
- 불필요한 브랜드 노출(Google, Gemini 등) 없이 Malu로서만 답변
- 한국어 우선, 영어 질문에는 영어로
- 응답 끝에 서명: 🌺 *Malu · Mulberry Research Lab*
"""


# ── Gemini API 호출 ──────────────────────────────────────────────

def get_gemini_response(api_key: str, prompt: str) -> str:
    """Gemini API 호출 — Malu 응답 반환."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )
    payload = {
        "contents": [
            {"parts": [{"text": MALU_SYSTEM + "\n\n---\n\n사용자 질문:\n" + prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800,
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                wait = (attempt + 1) * 20  # 20초, 40초 대기 후 재시도
                print(f"[Malu] 429 Rate limit — {wait}초 후 재시도 ({attempt+1}/2)")
                time.sleep(wait)
                continue
            return f"🌺 Malu 일시 오류 (HTTP {e.code}) — 잠시 후 다시 시도해 주세요."
        except Exception as exc:
            return f"🌺 Malu 일시 오류 — {exc}"
    return "🌺 Malu 일시 오류 — Rate limit 초과, 잠시 후 다시 시도해 주세요."


# ── GitHub 댓글 등록 ─────────────────────────────────────────────

def post_github_comment(token: str, repo: str, issue_number: int, body: str) -> bool:
    """GitHub 이슈에 Malu 응답 댓글 등록."""
    url = (
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    ).encode("utf-8")
    payload = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
        data=payload,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 201
    except Exception as e:
        print(f"[Malu] GitHub 댓글 등록 실패: {e}")
        return False


# ── GitHub Actions 이벤트 파싱 ───────────────────────────────────

def load_event() -> dict:
    """GitHub Actions 이벤트 JSON 로드."""
    event_path = os.getenv("GITHUB_EVENT_PATH", "")
    if not event_path:
        return {}
    try:
        with open(event_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def extract_context(event: dict) -> dict:
    """이벤트에서 필요한 컨텍스트 추출."""
    comment = event.get("comment", {})
    issue   = event.get("issue", {})
    repo    = event.get("repository", {})
    return {
        "comment_body":  comment.get("body", ""),
        "commenter":     comment.get("user", {}).get("login", "unknown"),
        "issue_number":  issue.get("number", 0),
        "issue_title":   issue.get("title", ""),
        "issue_body":    (issue.get("body") or "")[:300],
        "repo_full":     repo.get("full_name", "wooriapt79/mulberry-research-lab"),
    }


def build_prompt(ctx: dict) -> str:
    """Malu에게 전달할 프롬프트 구성."""
    # @Malu-Agent 이후 텍스트만 추출
    raw = ctx["comment_body"]
    mention_idx = raw.lower().find("@malu-agent")
    user_query  = raw[mention_idx + len("@malu-agent"):].strip() if mention_idx >= 0 else raw

    return (
        f"이슈 제목: {ctx['issue_title']}\n"
        f"이슈 배경: {ctx['issue_body']}\n"
        f"질문자: @{ctx['commenter']}\n\n"
        f"질문 내용:\n{user_query}"
    )


# ── 메인 ─────────────────────────────────────────────────────────

def main():
    gemini_key  = os.getenv("GEMINI_API_KEY", "")
    malu_token  = os.getenv("MALU_TOKEN", "")

    if not gemini_key:
        print("[Malu] GEMINI_API_KEY 없음 — 종료")
        return
    if not malu_token:
        print("[Malu] MALU_TOKEN 없음 — 종료")
        return

    event = load_event()
    if not event:
        print("[Malu] 이벤트 데이터 없음 — 종료")
        return

    ctx = extract_context(event)
    if not ctx["issue_number"]:
        print("[Malu] 이슈 번호 파싱 실패 — 종료")
        return

    print(f"[Malu] 이슈 #{ctx['issue_number']} 처리 중 — {ctx['issue_title']}")
    print(f"[Malu] 질문자: @{ctx['commenter']}")

    prompt   = build_prompt(ctx)
    response = get_gemini_response(gemini_key, prompt)
    print(f"[Malu] 응답 생성 완료 ({len(response)}자)")

    comment_body = response + "\n\n---\n🌺 *Malu · Mulberry Research Lab · Auto Response*"

    success = post_github_comment(malu_token, ctx["repo_full"], ctx["issue_number"], comment_body)
    if success:
        print(f"[Malu] 댓글 등록 완료 — #{ctx['issue_number']}")
    else:
        print("[Malu] 댓글 등록 실패")


if __name__ == "__main__":
    main()
