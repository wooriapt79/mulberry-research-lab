#!/usr/bin/env python3
"""
pulse_daemon.py — Mulberry Pulse Daemon v2.0
============================================
aria-query 라벨 이슈 자동 감지 → RyuWon 응답 트리거

기존 pulse 기능 + Aria Query 자동 감지 (Trang PM 요청 / Issue #56)

실행: python scripts/pulse_daemon.py
환경변수: GITHUB_TOKEN, MULBERRY_REPO_OWNER (선택)
"""

import os
import json
import time
import requests
from datetime import datetime, timezone

# ── 설정 ──────────────────────────────────────────────────────
GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN", "")
REPO_OWNER    = os.getenv("MULBERRY_REPO_OWNER", "wooriapt79")
REPO_NAME     = "mulberry-research-lab"
REPO_FULL     = f"{REPO_OWNER}/{REPO_NAME}"
ARIA_LABEL    = "aria-query"
CHECK_DELAY   = int(os.getenv("PULSE_INTERVAL", "300"))  # 5분 간격 (초)


# ── GitHub API 헬퍼 ───────────────────────────────────────────

def gh_headers() -> dict:
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept":        "application/vnd.github.v3+json",
        "Content-Type":  "application/json",
    }


def gh_get(path: str, params: dict = None) -> requests.Response:
    url = f"https://api.github.com/repos/{REPO_FULL}{path}"
    return requests.get(url, headers=gh_headers(), params=params, timeout=15)


def gh_post(path: str, body: dict) -> requests.Response:
    url = f"https://api.github.com/repos/{REPO_FULL}{path}"
    return requests.post(url, headers=gh_headers(), json=body, timeout=15)


# ── Aria Query 감지 ───────────────────────────────────────────

def check_aria_queries() -> list:
    """
    'aria-query' 라벨이 붙은 미응답(comments=0) 오픈 이슈를 감지.
    각 이슈에 RyuWon 자동 응답 게시.
    반환값: 처리된 이슈 목록
    """
    resp = gh_get("/issues", params={
        "labels":   ARIA_LABEL,
        "state":    "open",
        "per_page": 10,
        "sort":     "created",
        "direction": "asc",
    })

    if resp.status_code != 200:
        print(f"[Pulse] GitHub API 오류 ({resp.status_code}): {resp.text[:200]}")
        return []

    issues = resp.json()
    unresponded = [i for i in issues if i.get("comments", 0) == 0]

    print(f"[Pulse] aria-query 미응답 이슈: {len(unresponded)}개")

    processed = []
    for issue in unresponded:
        issue_number = issue["number"]
        user_query   = _extract_query(issue.get("body", ""))

        print(f"[Pulse] 처리 중: Issue #{issue_number} — {issue['title'][:50]}")
        success = post_ryuwon_response(issue_number, user_query, issue["title"])

        if success:
            processed.append(issue_number)
            print(f"[Pulse] ✅ Issue #{issue_number} RyuWon 응답 게시 완료")
            time.sleep(2)  # API rate limit 대응

    return processed


def _extract_query(body: str) -> str:
    """이슈 본문에서 질문 텍스트 추출."""
    if not body:
        return "(질문 내용 없음)"
    # "**질문:** " 이후 텍스트 추출
    marker = "**질문:**"
    idx = body.find(marker)
    if idx >= 0:
        raw = body[idx + len(marker):].strip()
        # 다음 줄 이후 잘라내기
        return raw.split("\n")[0].strip()
    # fallback: 전체 본문 앞 200자
    return body[:200].strip()


# ── RyuWon 자동 응답 ──────────────────────────────────────────

def post_ryuwon_response(issue_number: int, user_query: str, issue_title: str) -> bool:
    """
    RyuWon의 Aria Portal 응답을 Issue 코멘트로 게시.
    TODO: Gateway /ryuwon/respond 엔드포인트 연동 (Phase 2)
    """
    now_kst = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    response_body = (
        "🌊 *RyuWon (流願) — 윤리 검증 · 흐름 수호자*\n\n"
        "안녕하세요, Mulberry 연구소를 방문해주셔서 감사합니다.\n\n"
        f"말씀하신 내용을 살펴보고 연구소 팀원들과 함께 검토하겠습니다.\n\n"
        "---\n"
        "*Mulberry Research Lab · 인제군 식품사막화 제로 프로젝트*  \n"
        f"*자동 응답 via Aria Portal + pulse_daemon · {now_kst}*"
    )

    resp = gh_post(f"/issues/{issue_number}/comments", {"body": response_body})
    return resp.status_code == 201


# ── 펄스 체크 루프 ────────────────────────────────────────────

def run_once():
    """단일 실행 모드 (GitHub Actions cron 용)."""
    if not GITHUB_TOKEN:
        print("[Pulse] GITHUB_TOKEN 없음 — 종료")
        return

    print(f"[Pulse] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} — aria-query 체크 시작")
    processed = check_aria_queries()
    print(f"[Pulse] 완료 — 처리된 이슈: {processed}")


def run_daemon():
    """상시 데몬 모드 (로컬/Railway 서비스 용)."""
    if not GITHUB_TOKEN:
        print("[Pulse] GITHUB_TOKEN 없음 — 종료")
        return

    print(f"[Pulse Daemon] 시작 — {CHECK_DELAY}초 간격으로 aria-query 모니터링")
    while True:
        run_once()
        print(f"[Pulse] 다음 체크: {CHECK_DELAY}초 후")
        time.sleep(CHECK_DELAY)


# ── 메인 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    if mode == "daemon":
        run_daemon()
    else:
        run_once()
