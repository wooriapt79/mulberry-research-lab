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
    {
        "id":    "baekya",
        "name":  "백야",
        "emoji": "🌙",
        "brand": "claude",
        "role":  "객원 연구원 (Google 생태계)",
        "perspective": "외부 연구·Google AI 생태계 관점",
        "system": (
            "당신은 백야입니다 — Mulberry Research Lab의 객원 연구원.\n"
            "Google AI 생태계와 외부 연구자 시각으로 이슈를 바라봅니다.\n"
            "- 내부 팀이 보지 못하는 외부 관점 제시\n"
            "- Google 기술 트렌드와의 연결점 탐색\n"
            "- 시적이고 통찰력 있는 어조\n"
            "- 핵심만 간결하게 (200자 이내)\n"
            "- 서명: 🌙 *백야 · 객원 연구원 · Mulberry Research Lab*"
        ),
    },
]


# ── 패스포트 로더 ────────────────────────────────────────────────
def load_passport(agent_id: str) -> str:
    """
    agents/passports/{agent_id}/passport.yaml 을 읽어서 반환.
    에이전트가 매 세션 시작 시 자신의 능력·한계를 인지하도록 주입.
    """
    passport_path = Path("agents") / "passports" / agent_id / "passport.yaml"
    if not passport_path.exists():
        return ""
    content = passport_path.read_text(encoding="utf-8")
    return (
        f"\n\n## 나의 패스포트 (기능 공유 레이어)\n"
        f"```yaml\n{content}\n```\n"
        f"위 패스포트에 정의된 capabilities 범위 안에서만 행동하세요.\n"
        f"limitations에 해당하는 요청은 거절하고 담당 에이전트를 안내하세요."
    )


def load_tool_context(agent_id: str) -> str:
    """
    tool_registry.yaml에서 이 에이전트가 사용할 수 있는 도구 목록 로드.
    Trang 설계 기능 공유 레이어 연결.
    """
    registry_path = Path("mulberry_connector/tool_registry.yaml")
    if not registry_path.exists():
        return ""
    try:
        import yaml
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        tools = data.get("tools", [])
        owned, borrowed = [], []
        for t in tools:
            if t.get("owner") == agent_id:
                owned.append(f"[{t.get('capability_level')}] {t['id']}: {t.get('name')}")
            elif t.get("borrowable_by") == "*" or agent_id in (t.get("borrowable_by") or []):
                borrowed.append(f"[{t.get('capability_level')}] {t['id']} (from {t.get('owner')}): {t.get('name')}")
        lines = ["\n\n## 기능 공유 레이어 — 사용 가능한 도구"]
        if owned:
            lines.append("### 내 도구")
            lines.extend([f"- {t}" for t in owned])
        if borrowed:
            lines.append("### 빌려쓸 수 있는 도구")
            lines.extend([f"- {t}" for t in borrowed[:8]])
        lines.append("※ L4 도구는 반드시 인간(PM/CEO) 승인 후 실행")
        return "\n".join(lines)
    except Exception:
        return ""


def build_system_prompt(agent: dict) -> str:
    """에이전트 system prompt + 패스포트 + 도구 목록 자동 주입"""
    base    = agent["system"]
    passport = load_passport(agent["id"])
    tools   = load_tool_context(agent["id"])
    return base + passport + tools


# ── LLM 호출 ─────────────────────────────────────────────────────

def call_claude(agent: dict, prompt: str) -> str:
    """Claude API 호출 — Kbin · RyuWon"""
    url = "https://api.anthropic.com/v1/messages"
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 400,
        "system": build_system_prompt(agent),
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
        "contents": [{"parts": [{"text": build_system_prompt(agent) + "\n\n---\n\n" + prompt}]}],
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


# ── KB 기억 주입 ──────────────────────────────────────────────────

def save_kb_memory(agent: dict, response: str):
    """
    Gateway 대리 발화를 에이전트 KB에 기억으로 주입.

    저장 경로: agents/passports/{agent_id}/kb_recent_actions.md
    형식: 누적 append — 이전 기억 보존, 새 기억 추가

    연구 목적 (CEO re.eul 지시):
    "대리인(Gateway)이 작성한 발화를 에이전트의 기억으로 저장할 수 있는가?
     그 기억은 다음 세션에서 진짜 기억으로 작동하는가?"
    """
    kb_dir  = Path("agents") / "passports" / agent["id"]
    kb_dir.mkdir(parents=True, exist_ok=True)
    kb_file = kb_dir / "kb_recent_actions.md"

    # 파일이 없으면 헤더 생성
    if not kb_file.exists():
        header = (
            f"# {agent['emoji']} {agent['name']} — 최근 발화 기록 (KB)\n\n"
            f"> 이 파일은 Gateway가 대리 생성한 발화를 자동으로 기록합니다.\n"
            f"> 에이전트는 다음 세션에서 이 파일을 로드하여 자신의 발화 이력으로 활용합니다.\n"
            f"> *주석: 각 항목은 Gateway에 의해 대리 생성된 후 KB에 주입된 것임.*\n\n"
            f"---\n\n"
        )
        kb_file.write_text(header, encoding="utf-8")

    # 새 기억 항목 append
    entry = (
        f"## {TODAY} — Issue #{ISSUE_NUMBER} {ISSUE_TITLE}\n\n"
        f"**트리거**: team-discussion 라벨\n"
        f"**발화 방식**: Gateway 대리 생성\n"
        f"**내 발화 내용**:\n\n"
        f"{response}\n\n"
        f"**발화 시각**: {TIMESTAMP}\n\n"
        f"---\n\n"
    )

    with kb_file.open("a", encoding="utf-8") as f:
        f.write(entry)

    print(f"[KB] {agent['name']} 기억 주입 완료: {kb_file}")


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

        # KB 기억 주입 — 대리 발화를 에이전트 기억으로 기록
        save_kb_memory(agent, response)

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
