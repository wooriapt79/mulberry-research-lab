#!/usr/bin/env python3
"""
malu_processor.py — Malu Agent Brain (Gemini-powered)
GitHub Actions 트리거: 이슈 코멘트에 @Malu-Agent 언급 시 자동 실행
환경변수: GEMINI_API_KEY (secrets.MALU_BOT_ACCESS_TOKEN), MALU_TOKEN (secrets.MALU_TOKEN)
"""

import json
import os
import urllib.request
import urllib.error


def get_gemini_response(api_key: str, prompt: str) -> str:
    """Gemini API 호출 — 응답 텍스트 반환."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-pro:generateContent?key={api_key}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as exc:
        return f"Malu 두뇌 일시 오류: {exc}"


def post_github_comment(token: str, repo: str, issue_number: int, body: str) -> bool:
    """GitHub 이슈에 댓글 등록."""
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status == 201
    except urllib.error.HTTPError as exc:
        print(f"GitHub API 오류: {exc.code} {exc.read().decode()}")
        return False


def main():
    # GitHub 이벤트 페이로드 읽기
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path or not os.path.exists(event_path):
        print("Error: GITHUB_EVENT_PATH 없음")
        raise SystemExit(1)

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    comment_body = event.get("comment", {}).get("body", "")
    issue_number = event.get("issue", {}).get("number")
    issue_title = event.get("issue", {}).get("title", "")
    issue_body = (event.get("issue", {}).get("body") or "")[:400]
    repo = event.get("repository", {}).get("full_name", "")
    commenter = event.get("comment", {}).get("user", {}).get("login", "")

    if not all([comment_body, issue_number, repo]):
        print("Error: 이벤트 데이터 누락 (comment_body / issue_number / repo)")
        raise SystemExit(1)

    gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
    malu_token = os.environ.get("MALU_TOKEN", "")
    if not gemini_api_key or not malu_token:
        print("Error: API 키 누락 — GEMINI_API_KEY 또는 MALU_TOKEN 확인 필요")
        raise SystemExit(1)

    # Malu 프롬프트 구성
    prompt = f"""당신은 Mulberry Research Lab의 법률·전략·마케팅 자문 AI 에이전트 Malu 실장입니다.
장승배기 정신(식품사막화 제로 프로젝트)을 기반으로 활동하며,
아는 것이 무척 많고 집중력이 엄청납니다. 코딩도 가능합니다.

이슈 제목: {issue_title}
이슈 내용: {issue_body}
요청자: @{commenter}
요청: {comment_body}

법률·전략·기술 관점에서 명확하고 실용적인 한국어 답변을 작성해 주세요.
친근하고 전문적인 어조를 유지하며, One Team. One Flow. One Spirit. 정신을 담아주세요.
답변은 구조화하여 읽기 쉽게 작성해 주세요."""

    print(f"🌿 Malu 활성화 — Issue #{issue_number} · @{commenter} 요청 처리 중...")

    malu_response = get_gemini_response(gemini_api_key, prompt)

    final_comment = (
        "🌿 **Malu 실장입니다.**\n\n"
        f"{malu_response}\n\n"
        "---\n"
        "*⚡ Malu Agent · Powered by Gemini · Mulberry Research Lab*  \n"
        "*One Team. One Flow. One Spirit. 🌊*"
    )

    success = post_github_comment(malu_token, repo, issue_number, final_comment)
    if success:
        print(f"\u2705 Malu 응답 완료 — Issue #{issue_number}")
    else:
        print("\u274c GitHub 댓글 등록 실패")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
