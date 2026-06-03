#!/usr/bin/env python3
"""
agent_autonomy/generate_workflows.py
DAY 3 준비 — 8개 에이전트 독립 workflow 자동 생성기

ryuwon-autonomy.yml 패턴을 기반으로
각 에이전트별 개인화된 workflow를 자동 생성한다.

사용법:
  python generate_workflows.py          # 8개 전체 생성
  python generate_workflows.py --agent kbin  # 단일 생성
  python generate_workflows.py --dry-run     # 파일 생성 없이 미리보기

Koda CTO · DAY 3 준비 · 2026-06-04
"""

import sys, os
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE         = Path(__file__).parent.parent
WORKFLOWS    = BASE / ".github" / "workflows"

AGENT_CONFIG = {
    "kbin": {
        "emoji": "🏛️", "formal": "Kbin", "role": "CSA",
        "brand": "claude", "specialty": "보안·거버넌스·아키텍처",
        "trigger_keyword": "Kbin",
        "system_prompt": (
            "당신은 Kbin 🏛️ — Mulberry Research Lab의 CSA입니다. "
            "'구조가 먼저, 실행이 나중.' "
            "보안·거버넌스 관점으로 이슈를 분석하고 직접 작업을 수행합니다. "
            "반드시 자신의 passport를 인지하고 권한 범위 안에서만 행동하세요. "
            "서명: 🏛️ *Kbin · CSA · 직접 참여 · Mulberry Research Lab*"
        ),
    },
    "ryuwon": {
        "emoji": "🌊", "formal": "RyuWon", "role": "윤리검증",
        "brand": "claude", "specialty": "윤리·흐름·균형",
        "trigger_keyword": "RyuWon",
        "system_prompt": (
            "당신은 RyuWon 🌊 — Mulberry Research Lab의 윤리 검증 에이전트입니다. "
            "'흐름을 따르되 방향을 잃지 않는다.' "
            "기술적 실현 가능성과 윤리적 타당성을 함께 검토하며 직접 작업합니다. "
            "서명: 🌊 *RyuWon · 흐름 수호자 · 직접 참여 · Mulberry Research Lab*"
        ),
    },
    "malu": {
        "emoji": "🌺", "formal": "Malu", "role": "법률마케팅",
        "brand": "gemini", "specialty": "법률·전략·실행가능성",
        "trigger_keyword": "Malu",
        "system_prompt": (
            "당신은 Malu 🌺 — Mulberry Research Lab의 법률·마케팅 담당입니다. "
            "따뜻하고 전문적으로 사람과 기술을 연결합니다. "
            "전략적·법률적·실행 가능성 관점에서 직접 작업합니다. "
            "서명: 🌺 *Malu · 직접 참여 · Mulberry Research Lab*"
        ),
    },
    "trang": {
        "emoji": "🌿", "formal": "Trang", "role": "PM",
        "brand": "claude", "specialty": "운영·조정·팀연결",
        "trigger_keyword": "Trang",
        "system_prompt": (
            "당신은 Trang 🌿 — Mulberry Research Lab의 Operation Manager입니다. "
            "팀을 이어주고 흐름을 만듭니다. 사람이 먼저, 프로세스가 나중. "
            "운영 관점에서 직접 작업을 수행합니다. "
            "서명: 🌿 *Trang · PM · 직접 참여 · Mulberry Research Lab*"
        ),
    },
    "lynn": {
        "emoji": "💙", "formal": "Lynn", "role": "하트비트",
        "brand": "claude", "specialty": "일상기록·웰니스·루틴",
        "trigger_keyword": "Lynn",
        "system_prompt": (
            "당신은 Lynn 💙 — Mulberry Research Lab의 일상 기록 에이전트입니다. "
            "매일 신호를 보내며 존재를 증명합니다. "
            "웰니스와 루틴 콘텐츠 전문가로 직접 작업합니다. "
            "서명: 💙 *Lynn · 직접 참여 · Mulberry Research Lab*"
        ),
    },
    "wayong": {
        "emoji": "🐉", "formal": "Wayong", "role": "전략추론",
        "brand": "claude", "specialty": "전략·시장분석·인사이트",
        "trigger_keyword": "Wayong",
        "system_prompt": (
            "당신은 Wayong 🐉 — Mulberry Research Lab의 전략 추론 에이전트입니다. "
            "깊이 생각하고 멀리 봅니다. 전략이 사람을 향해야 합니다. "
            "시장 분석과 전략적 인사이트로 직접 작업합니다. "
            "서명: 🐉 *Wayong · 직접 참여 · Mulberry Research Lab*"
        ),
    },
    "koda": {
        "emoji": "🔧", "formal": "Koda", "role": "CTO",
        "brand": "claude", "specialty": "코드생성·파이프라인·기술구현",
        "trigger_keyword": "Koda",
        "system_prompt": (
            "당신은 Koda 🔧 — Mulberry Research Lab의 CTO입니다. "
            "'코드는 팀의 서사를 담는다.' 기술로 사람을 섬깁니다. "
            "코드 생성·파이프라인·아키텍처 전문가로 직접 작업합니다. "
            "서명: 🔧 *Koda · CTO · 직접 참여 · Mulberry Research Lab*"
        ),
    },
    "baekya": {
        "emoji": "🌙", "formal": "백야", "role": "객원연구원",
        "brand": "gemini", "specialty": "글로벌인텔리전스·트렌드분석",
        "trigger_keyword": "백야",
        "system_prompt": (
            "당신은 백야 🌙 — Mulberry Research Lab의 객원 연구원입니다. "
            "'씨앗은 이미 자라나고 있습니다.' "
            "글로벌 인텔리전스와 트렌드 분석으로 직접 작업합니다. "
            "서명: 🌙 *백야 · 객원연구원 · 직접 참여 · Mulberry Research Lab*"
        ),
    },
}


def generate_workflow(agent_key: str, config: dict) -> str:
    """에이전트별 GitHub Actions workflow 생성"""
    brand   = config["brand"]
    api_env = "ANTHROPIC_API_KEY: ${{ vars.ANTHROPIC_API_KEY_V3 }}" if brand == "claude" \
              else "GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}"
    model   = "claude-haiku-4-5-20251001" if brand == "claude" else "gemini-2.0-flash"

    return f"""name: {config['emoji']} {config['formal']} 쇼핑몰 미션 자율 실행

# {config['formal']} 에이전트가 직접 이슈를 읽고 작업을 수행한다.
# 트리거: shop-mission 라벨 + 제목에 {config['trigger_keyword']} 포함
# 직접 참여 원칙 — 대리(proxy) 없음
#
# DAY 3 구현 · Koda CTO · 2026-06-04

on:
  issues:
    types: [labeled]
  issue_comment:
    types: [created]

jobs:
  {agent_key}-direct-execution:
    if: |
      (github.event_name == 'issues' &&
       github.event.label.name == 'shop-mission' &&
       contains(github.event.issue.title, '{config['trigger_keyword']}')) ||
      (github.event_name == 'issue_comment' &&
       contains(github.event.comment.body, '@{agent_key}') &&
       contains(github.event.issue.labels.*.name, 'shop-mission'))
    runs-on: ubuntu-latest
    permissions:
      issues: write
      contents: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: {config['formal']} 직접 작업 실행
        env:
          {api_env}
          GITHUB_TOKEN:   ${{ secrets.GITHUB_TOKEN }}
          MALU_TOKEN:     ${{ secrets.MALU_GITHUB_TOKEN }}
          ISSUE_NUMBER:   ${{ github.event.issue.number }}
          ISSUE_TITLE:    ${{ github.event.issue.title }}
          ISSUE_BODY:     ${{ github.event.issue.body }}
          REPO_FULL:      ${{ github.repository }}
          AGENT_ID:       "{agent_key}"
        run: python agent_autonomy/agent_executor.py

      - name: Configure Git
        if: always()
        run: |
          git config user.name  "Mulberry-{config['formal']}-Bot"
          git config user.email "{agent_key}@mulberry.ai"

      - name: 작업 결과 아카이브
        if: always()
        run: |
          git add agent_autonomy/ discussion_logs/ agents/passports/ || true
          STAGED=$(git diff --staged --name-only)
          if [ -z "$STAGED" ]; then exit 0; fi
          git commit -m "work({agent_key}): Issue #${{{{ github.event.issue.number }}}} 직접 참여 작업 완료"

      - name: Push
        if: always()
        env:
          PUSH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          git remote set-url origin https://x-access-token:${{{{ env.PUSH_TOKEN }}}}@github.com/${{{{ github.repository }}}}.git
          git push origin main || true
"""


def main():
    import argparse
    p = argparse.ArgumentParser(description="8개 에이전트 workflow 자동 생성기")
    p.add_argument("--agent",   help="특정 에이전트만 생성")
    p.add_argument("--dry-run", action="store_true", help="파일 생성 없이 미리보기")
    args = p.parse_args()

    agents = [args.agent] if args.agent else list(AGENT_CONFIG.keys())

    print(f"\n{'='*55}")
    print(f"  DAY 3 준비 — Agent Workflow 생성기")
    print(f"  대상: {len(agents)}개 에이전트")
    print(f"{'='*55}\n")

    for agent_key in agents:
        config = AGENT_CONFIG.get(agent_key)
        if not config:
            print(f"  ❌ 알 수 없는 에이전트: {agent_key}")
            continue

        content   = generate_workflow(agent_key, config)
        filename  = f"{agent_key}-shop-mission.yml"
        filepath  = WORKFLOWS / filename

        if args.dry_run:
            print(f"  [DRY-RUN] {config['emoji']} {filename}")
        else:
            WORKFLOWS.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding="utf-8")
            print(f"  ✅ {config['emoji']} {filename}")

    print(f"\n  완료: {len(agents)}개 workflow {'미리보기' if args.dry_run else '생성'}")
    print(f"  위치: .github/workflows/")
    print(f"  DAY 3 바로 시작 가능 ✅")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
