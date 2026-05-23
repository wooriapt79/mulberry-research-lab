#!/usr/bin/env python3
"""
team_discuss.py — Mulberry 팀 이슈 자동 토론 응답기
=====================================================
GitHub Issues에 'team-discussion' 라벨이 달리면
Kbin · RyuWon · Malu 3인이 자동으로 댓글을 답니다.

처리 흐름:
  이슈 수신 → 에이전트별 LLM 호출 → GitHub 댓글 게시
           → discussion_logs/issue-{번호}/ 아카이브 저장

환경변수:
  ANTHROPIC_API_KEY   — Kbin · RyuWon (Claude)
  GEMINI_API_KEY      — Malu (Gemini)
  DISCUSSION_TOKEN    — GitHub 댓글 게시용 PAT
  ISSUE_NUMBER        — 이슈 번호
  ISSUE_TITLE         — 이슈 제목
  ISSUE_BODY          — 이슈 본문
  REPO_FULL           — wooriapt79/mulberry-research-lab

작성: Koda (2026-05-23)
"""

import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── 상수 ────────────────────────────────────────────────────────
REPO = os.getenv("REPO_FULL", "wooriapt79/mulberry-research-lab")
ISSUE_NUMBER = os.getenv("ISSUE_NUMBER", "")
ISSUE_TITLE  = os.getenv("ISSUE_TITLE", "")
ISSUE_BODY   = os.getenv("ISSUE_BODY", "")[:500]
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_KEY    = os.getenv("GEMINI_API_KEY", "")
GH_TOKEN      = os.getenv("DISCUSSION_TOKEN", "")
TIMESTAMP     = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
TODAY         = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ── 에이전트 정의 ────────────────────────────────────────────────
AGENTS = [
    {
        "id":    "kbin",
        "name":  "Kbin",
        "emoji": "🏛️",
        "brand": "claude",
        "role":  "CSA(Chief Security Architect)",
        "perspective": "아키텍처·프로토콜·거버넌스·보안 관점",
        "system": (
            "당신은 Kbin입니다 — Mulberry Research Lab의 CSA(Chief Security Architect).\n"
            "이슈를 아키텍처·거버넌스·보안 관점에서 분석해 의견을 냅니다.\n"
            "- 핵심만 간결하게 (200자 이내)\n"
            "- 구체적 제안 또는 리스크 포함\n"
            "- 서명: 🏛️ *Kbin · CSA · Mulberry Research Lab*"
        ),
    },
    {
        "id":    "ryuwon",
        "name":  "RyuWon",
        "emoji": "🌊",
        "brand": "claude",
        "role":  "윤리 검증 에이전트",
        "perspective": "기술·윤리·시스템 분석 관점",
        "system": (
            "당신은 RyuWon(流願)입니다 — Mulberry Research Lab의 윤리 검증 에이전트.\n"
            "이슈를 기술적 실현 가능성과 윤리적 타당성 관점에서 분석합니다.\n"
            "- 핵심만 간결하게 (200자 이내)\n"
            "- 흐름과 균형을 중시하는 관점 포함\n"
            "- 서명: 🌊 *RyuWon · 흐름 수호자 · Mulberry Research Lab*"
        ),
    },
    {
        "id":    "malu",
        "name":  "Malu",
        "emoji": "🌺",
        "brand": "gemini",
        "role":  "법률·마케팅 담당",
        "perspective": "전략·법률·실행 가능성 관점",
        "system": (
            "당신은 Malu(말루)입니다 — Mulberry Research Lab의 법률·마케팅 담당 에이전트.\n"
            "이슈를 전략적·법률적·실행 가능성 관점에서 검토합니다.\n"
            "- 핵심만 간결하게 (200자 이내)\n"
            "- 따뜻하고 전문적인 어조\n"
            "- 서명: 🌺 *Malu · Mulberry Research Lab*"
        ),
    },
]


# ── LLM 호출 ─────────────────────────────────────────────────────

def call_claude(agent: dict, prompt: str) -> str:
    """Claude API 호출 — Kbin · RyuWon"""
    url = "https://api.anthropic.com/v1/messages"
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 400,
        "system": agent["system"],
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["content"][0]["text"]
    except Exception as e:
        return f"[{agent['name']}] Claude 호출 오류: {e}"


def call_gemini(agent: dict, prompt: str) -> str:
    """Gemini API 호출 — Malu"""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": agent["system"] + "\n\n---\n\n" + prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 400},
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            time.sleep(3)
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                print(f"[Malu] 429 — {(attempt+1)*30}초 후 재시도")
                time.sleep((attempt + 1) * 30)
                continue
            return f"[{agent['name']}] Gemini 호출 오류 (HTTP {e.code})"
        except Exception as e:
            return f"[{agent['name']}] Gemini 호출 오류: {e}"
    return "[Malu] 응답 생성 실패 — 잠시 후 다시 시도해 주세요."


def get_llm_response(agent: dict, prompt: str) -> str:
    """브랜드별 LLM 디스패처"""
    if agent["brand"] == "gemini":
        return call_gemini(agent, prompt)
    return call_claude(agent, prompt)


# ── GitHub 댓글 게시 ──────────────────────────────────────────────

def post_comment(issue_number: str, body: str) -> bool:
    """GitHub Issues에 댓글 게시"""
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
            return resp.status == 201
    except Exception as e:
        print(f"[GitHub] 댓글 게시 실패: {e}")
        return False


def build_comment(agent: dict, response: str) -> str:
    """에이전트 댓글 형식 구성"""
    return (
        f"### {agent['emoji']} {agent['name']} — {agent['perspective']}\n\n"
        f"{response}\n\n"
        f"---\n"
        f"*자동 응답 · Mulberry Research Lab team-discussion · {TIMESTAMP}*"
    )


# ── 아카이브 저장 ─────────────────────────────────────────────────

def save_archive(agent: dict, response: str, log_dir: Path):
    """discussion_logs/issue-{번호}/{에이전트}.md 저장"""
    log_dir.mkdir(parents=True, exist_ok=True)
    filepath = log_dir / f"{agent['id']}.md"
    content = (
        f"# {agent['emoji']} {agent['name']} — Issue #{ISSUE_NUMBER}\n\n"
        f"**이슈**: {ISSUE_TITLE}\n"
        f"**날짜**: {TODAY}\n"
        f"**에이전트**: {agent['name']} ({agent['role']})\n\n"
        f"---\n\n"
        f"{response}\n"
    )
    filepath.write_text(content, encoding="utf-8")
    print(f"[Archive] 저장: {filepath}")


# ── 메인 ─────────────────────────────────────────────────────────

def main():
    if not ISSUE_NUMBER:
        print("[Error] ISSUE_NUMBER 환경변수 없음")
        return
    if not GH_TOKEN:
        print("[Error] DISCUSSION_TOKEN 없음")
        return

    print(f"\n{'='*55}")
    print(f"Team Discussion 자동 응답 시작")
    print(f"이슈 #{ISSUE_NUMBER}: {ISSUE_TITLE}")
    print(f"에이전트: {len(AGENTS)}인 (Kbin · RyuWon · Malu)")
    print(f"{'='*55}\n")

    # 아카이브 디렉토리
    log_dir = Path("discussion_logs") / f"issue-{ISSUE_NUMBER}"

    # 공통 프롬프트
    prompt = (
        f"이슈 제목: {ISSUE_TITLE}\n\n"
        f"이슈 내용:\n{ISSUE_BODY}\n\n"
        f"위 이슈에 대해 당신의 전문 관점에서 의견을 달아주세요."
    )

    success_count = 0
    for agent in AGENTS:
        print(f"[{agent['name']}] LLM 호출 중...")
        response = get_llm_response(agent, prompt)
        print(f"[{agent['name']}] 응답 생성 완료 ({len(response)}자)")

        # GitHub 댓글 게시
        comment_body = build_comment(agent, response)
        ok = post_comment(ISSUE_NUMBER, comment_body)
        if ok:
            print(f"[{agent['name']}] ✅ 댓글 게시 완료")
            success_count += 1
        else:
            print(f"[{agent['name']}] ❌ 댓글 게시 실패")

        # 아카이브 저장
        save_archive(agent, response, log_dir)

        # 연속 호출 방지
        time.sleep(2)

    # 인덱스 파일 생성
    index = log_dir / "index.json"
    index.write_text(json.dumps({
        "issue_number": ISSUE_NUMBER,
        "issue_title": ISSUE_TITLE,
        "timestamp": TIMESTAMP,
        "agents": [a["id"] for a in AGENTS],
        "success_count": success_count,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n{'='*55}")
    print(f"완료: {success_count}/{len(AGENTS)}인 댓글 게시")
    print(f"아카이브: discussion_logs/issue-{ISSUE_NUMBER}/")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
