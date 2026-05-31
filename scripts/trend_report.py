#!/usr/bin/env python3
"""
scripts/trend_report.py — Mulberry 월간 기술 트렌드 리포트 자동 생성
====================================================================
매월 1일 GitHub Actions에서 실행:
  1. Claude API로 최신 AI 기술 트렌드 수집·정리
  2. GitHub 이슈 자동 생성
  3. team-discussion 라벨 부착 → 팀 자동 토론 시작

환경변수:
  ANTHROPIC_API_KEY  — Claude 호출
  GITHUB_TOKEN       — 이슈 생성

작성: Koda CTO · Mulberry Research Lab · 2026-05-31
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

REPO          = os.getenv("REPO_FULL", "wooriapt79/mulberry-research-lab")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GH_TOKEN      = os.getenv("GITHUB_TOKEN", "")
NOW           = datetime.now(timezone.utc)
YEAR_MONTH    = NOW.strftime("%Y년 %m월")
TODAY         = NOW.strftime("%Y-%m-%d")


# ── Claude 호출 ─────────────────────────────────────────────────────

def call_claude(prompt: str, system: str) -> str:
    url = "https://api.anthropic.com/v1/messages"
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 2000,
        "system": system,
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
        return f"Claude 호출 오류: {e}"


# ── 트렌드 리포트 생성 ───────────────────────────────────────────────

def generate_trend_report() -> str:
    system = """당신은 Mulberry Research Lab의 CTO Koda입니다.
AI·기술 트렌드를 분석하여 팀 토론용 월간 리포트를 작성합니다.
반드시 아래 형식을 지켜주세요. 한국어로 작성합니다."""

    prompt = f"""오늘은 {TODAY}입니다. {YEAR_MONTH} AI 기술 트렌드 리포트를 작성해주세요.

아래 형식으로 작성하세요:

## 📡 이달의 핵심 트렌드 (3가지)

각 트렌드마다:
- **트렌드명**: 한 줄 요약
- **무슨 일이**: 구체적 내용 (2~3줄)
- **Mulberry 관점**: 우리에게 위협인가, 기회인가, 참고할 것인가

## 🔍 주목할 기업·모델

최근 주목받는 AI 기업 또는 모델 2~3개, 기술 스펙 중심으로.

## 🌿 Mulberry 포지셔닝

현재 트렌드 속에서 Mulberry의 강점과 차별점.

## 💡 이달의 토론 주제 (3가지)

팀이 토론할 수 있는 구체적인 질문 3개.

---
형식을 정확히 지키고, 실용적이고 구체적으로 작성하세요."""

    return call_claude(prompt, system)


# ── 이슈 본문 구성 ───────────────────────────────────────────────────

def build_issue_body(report_content: str) -> str:
    return f"""## 🔭 {YEAR_MONTH} Mulberry 기술 트렌드 리포트

> **목적**: 외부 기술 환경 파악 → Mulberry 포지셔닝 점검
> **주기**: 매월 1일 자동 생성
> **참여**: Kbin · RyuWon · Malu · 백야(객원) 자동 토론 + Koda CTO 종합

---

{report_content}

---

## 💬 팀 토론 요청

위 내용을 바탕으로 각자의 전문 관점에서 의견을 달아주세요.

- **Kbin** 🏛️ — 아키텍처·보안 관점에서 우리가 대응해야 할 것은?
- **RyuWon** 🌊 — 이 트렌드가 장승배기 정신과 어떻게 연결되는가?
- **Malu** 🌺 — 시장·전략 관점에서 B2B 기회가 있는가?
- **백야** 🌙 — Google 생태계·외부 연구 관점에서 본 이달의 핵심은?
- **Koda** 🔧 — 다음 달 개발 방향에 반영할 것은?

---

*자동 생성: Mulberry Tech Trend Bot · {TODAY}*
*🌿 One Team. One Flow. One Spirit.*
"""


# ── GitHub 이슈 생성 ─────────────────────────────────────────────────

def create_issue(title: str, body: str) -> dict:
    url = f"https://api.github.com/repos/{REPO}/issues"
    payload = json.dumps({
        "title": title,
        "body": body,
        "labels": ["team-discussion", "trend-report", "monthly"],
    }).encode("utf-8")
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
            result = json.loads(resp.read().decode("utf-8"))
            return {"success": True, "url": result.get("html_url"), "number": result.get("number")}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── 메인 ─────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"  Mulberry 월간 기술 트렌드 리포트")
    print(f"  {YEAR_MONTH} · {TODAY}")
    print(f"{'='*55}\n")

    if not ANTHROPIC_KEY:
        print("❌ ANTHROPIC_API_KEY 없음")
        sys.exit(1)
    if not GH_TOKEN:
        print("❌ GITHUB_TOKEN 없음")
        sys.exit(1)

    # 1. 트렌드 리포트 생성
    print("🤖 Claude로 트렌드 리포트 생성 중...")
    report_content = generate_trend_report()
    print(f"   완료 ({len(report_content)}자)\n")

    # 2. 이슈 본문 구성
    body = build_issue_body(report_content)
    title = f"🔭 [{YEAR_MONTH}] Mulberry 기술 트렌드 리포트 — 팀 토론"

    # 3. GitHub 이슈 생성
    print("📋 GitHub 이슈 생성 중...")
    result = create_issue(title, body)

    if result["success"]:
        print(f"✅ 이슈 생성 완료!")
        print(f"   #{result['number']}: {result['url']}")
        print(f"   → team-discussion 라벨로 팀 자동 토론 시작")
    else:
        print(f"❌ 이슈 생성 실패: {result['error']}")
        sys.exit(1)

    print(f"\n{'='*55}\n")


if __name__ == "__main__":
    main()
