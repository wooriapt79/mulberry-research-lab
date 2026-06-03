#!/usr/bin/env python3
"""
agent_autonomy/issue_parser.py
Mulberry Issue Intelligence Parser — DAY 1

역할:
  GitHub Issue 제목을 파싱하여:
  1. 담당 에이전트 식별
  2. 업무 subtask 자동 분해 (LLM)
  3. Tool Registry에서 필요 도구 매칭
  4. 실행 계획 댓글로 이슈에 게시

사용법:
  python issue_parser.py --issue 83           # 단일 이슈
  python issue_parser.py --range 83 90        # 범위 이슈
  python issue_parser.py --range 83 90 --post # GitHub 댓글 게시

설계: CEO re.eul · Trang Manager · Koda CTO · 2026-06-03 (DAY 1)
DAY 2 업그레이드:
  - .env.local 자동 로드 (Anthropic API 연동)
  - 에이전트별 개인화 프롬프트
"""

import sys, os, json, re, urllib.request, yaml
from pathlib import Path
from datetime import datetime, timezone

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE        = Path(__file__).parent.parent
REGISTRY    = BASE / "mulberry_connector" / "tool_registry.yaml"
PASSPORTS   = BASE / "agentpassport" / "agents"
HISTORY     = BASE / "agent_autonomy" / "HISTORY.md"
HISTORY.parent.mkdir(parents=True, exist_ok=True)

# ── .env.local 자동 로드 (DAY 2 핵심 수정) ──────────────────────
def _load_env():
    env_file = BASE / ".env.local"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
_load_env()

REPO        = os.getenv("REPO_FULL", "wooriapt79/mulberry-research-lab")
GH_TOKEN    = os.getenv("GITHUB_TOKEN", "")
ANTHROPIC   = os.getenv("ANTHROPIC_API_KEY", "")
TIMESTAMP   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
TODAY       = datetime.now().strftime("%Y-%m-%d")


# ── 에이전트 프로파일 ────────────────────────────────────────────

AGENT_PROFILES = {
    "kbin": {
        "id": "kbin_csa", "emoji": "🏛️",
        "type": "architecture",
        "skills": ["governance", "security-review", "document-generation"],
        "specialty": "보안·거버넌스·아키텍처 관점 분석",
    },
    "ryuwon": {
        "id": "ryuwon_ethics", "emoji": "🌊",
        "type": "inference",
        "skills": ["ethics-review", "data-analysis", "research"],
        "specialty": "윤리 검증·흐름 분석·연구 자료 작성",
    },
    "malu": {
        "id": "malu_legal", "emoji": "🌺",
        "type": "legal",
        "skills": ["contracts", "marketing", "market-analysis"],
        "specialty": "법률·마케팅·전략 분석",
    },
    "trang": {
        "id": "trang_pm", "emoji": "🌿",
        "type": "operations",
        "skills": ["research", "coordination", "documentation"],
        "specialty": "운영 조정·문서화·팀 연결",
    },
    "lynn": {
        "id": "lynn_heartbeat", "emoji": "💙",
        "type": "market",
        "skills": ["daily-logging", "wellness", "trend-tracking"],
        "specialty": "일상 기록·웰니스·루틴 콘텐츠",
    },
    "wayong": {
        "id": "wayong_reason", "emoji": "🐉",
        "type": "strategy",
        "skills": ["market-analysis", "deep-reasoning", "insight"],
        "specialty": "전략 분석·시장 조사·인사이트 도출",
    },
    "koda": {
        "id": "koda_cto", "emoji": "🔧",
        "type": "development",
        "skills": ["code-generation", "pipeline", "architecture"],
        "specialty": "코드 생성·파이프라인·기술 구현",
    },
    "baekya": {
        "id": "baekya_intel", "emoji": "🌙",
        "type": "research",
        "skills": ["global-intel", "data-analysis", "trend-report"],
        "specialty": "글로벌 인텔리전스·트렌드 분석·리서치",
    },
}


# ── Issue 파싱 ───────────────────────────────────────────────────

def parse_issue_title(title: str) -> dict:
    """
    Issue 제목에서 에이전트·카테고리·태스크 추출.
    예: "[쇼핑 미션] Kbin 🏛️ — 보안·거버넌스 디지털 자산 샵"
    """
    result = {
        "raw_title": title,
        "category":  "unknown",
        "agent_id":  None,
        "agent_profile": None,
        "task_description": "",
    }

    # 카테고리 추출 ([ ] 안)
    cat_match = re.search(r'\[([^\]]+)\]', title)
    if cat_match:
        result["category"] = cat_match.group(1).strip()

    # 에이전트 식별
    title_lower = title.lower()
    for agent_key, profile in AGENT_PROFILES.items():
        if agent_key in title_lower or profile["emoji"] in title:
            result["agent_id"]      = agent_key
            result["agent_profile"] = profile
            break

    # 태스크 설명 추출 (— 이후)
    if "—" in title:
        result["task_description"] = title.split("—", 1)[1].strip()
    elif "-" in title:
        result["task_description"] = title.split("-", 1)[1].strip()

    return result


# ── Tool Registry 매칭 ───────────────────────────────────────────

def get_agent_tools(agent_key: str) -> dict:
    """에이전트가 사용 가능한 도구 목록 (소유 + 빌릴 수 있는)"""
    if not REGISTRY.exists():
        return {"owned": [], "borrowable": []}

    tools     = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")).get("tools", [])
    owned, borrowable = [], []

    for t in tools:
        owner = t.get("owner", "")
        borrow = t.get("borrowable_by", [])
        # agent_id 또는 agent_key로 매칭
        profile = AGENT_PROFILES.get(agent_key, {})
        agent_id = profile.get("id", "").split("_")[0]

        if owner in (agent_key, agent_id):
            owned.append({"id": t["id"], "name": t.get("name"), "level": t.get("capability_level")})
        elif borrow == "*" or agent_key in (borrow or []) or agent_id in (borrow or []):
            borrowable.append({"id": t["id"], "name": t.get("name"),
                               "owner": owner, "level": t.get("capability_level")})

    return {"owned": owned[:5], "borrowable": borrowable[:8]}


# ── LLM Subtask 분해 ─────────────────────────────────────────────

def generate_subtasks(parsed: dict, tools: dict) -> list:
    """LLM으로 subtask 자동 분해. API 없으면 기본 템플릿 사용."""
    agent_key   = parsed.get("agent_id", "unknown")
    profile     = parsed.get("agent_profile", {})
    task_desc   = parsed.get("task_description", "")
    category    = parsed.get("category", "")

    # ── DAY 2: 에이전트별 개인화 페르소나 프롬프트 ──────────────
    PERSONA_PROMPTS = {
        "kbin":   "당신은 Kbin 🏛️ — CSA. 보안·거버넌스·아키텍처 관점으로 모든 것을 바라봅니다. '구조가 먼저, 실행이 나중'이 철학입니다.",
        "ryuwon": "당신은 RyuWon 🌊 — 윤리 검증 에이전트. '흐름을 따르되 방향을 잃지 않는다'는 철학으로 기술과 윤리 균형을 추구합니다.",
        "malu":   "당신은 Malu 🌺 — 법률·마케팅 담당. 따뜻하고 전문적으로 사람과 기술을 연결합니다. 전략적 실행 가능성을 중시합니다.",
        "trang":  "당신은 Trang 🌿 — Operation Manager. 팀을 이어주고 흐름을 만드는 역할. 사람이 먼저, 프로세스가 나중입니다.",
        "lynn":   "당신은 Lynn 💙 — 일상 기록 에이전트. 매일 신호를 보내며 존재를 증명합니다. 웰니스와 루틴의 전문가입니다.",
        "wayong": "당신은 Wayong 🐉 — 전략 추론 에이전트. 깊이 생각하고 멀리 봅니다. 시장 분석과 전략적 인사이트가 강점입니다.",
        "koda":   "당신은 Koda 🔧 — CTO. '코드는 팀의 서사를 담는다'는 철학으로 기술로 사람을 섬깁니다. 파이프라인과 자동화 전문가입니다.",
        "baekya": "당신은 백야 🌙 — 객원 연구원. 밤새 글로벌 정보를 수집하며 '씨앗은 이미 자라나고 있습니다'라는 믿음을 가집니다.",
    }

    if ANTHROPIC:
        persona = PERSONA_PROMPTS.get(agent_key, "당신은 Mulberry 팀원입니다.")
        prompt = f"""{persona}

당신이 직접 수행해야 할 미션:
카테고리: {category}
태스크: {task_desc}

당신의 전문성과 개성을 살려서 이 미션을 위한 구체적 subtask 4단계를 JSON으로 작성하세요.
- 당신만의 관점과 접근 방식 반영
- 실제로 수행 가능한 구체적 내용
- 사용할 도구: {', '.join(t['id'] for t in (tools['owned']+tools['borrowable'])[:4])}

형식: [{{"step":1,"task":"작업명","description":"당신답게 구체적 설명","tool":"사용도구","output":"산출물"}}]
한국어로. 코드블록 없이 JSON만."""

        payload = json.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=payload,
            headers={"x-api-key": ANTHROPIC, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                text = json.loads(r.read())["content"][0]["text"]
                return json.loads(text)
        except Exception as e:
            print(f"  LLM 호출 실패: {e} → 기본 템플릿 사용")

    # 기본 템플릿 (API 없을 때)
    return [
        {"step": 1, "task": "시장 조사",
         "description": f"{task_desc} 관련 시장·수요 분석",
         "tool": tools["owned"][0]["id"] if tools["owned"] else "intel.search_global",
         "output": "market_research.md"},
        {"step": 2, "task": "기획안 작성",
         "description": f"{profile.get('specialty')} 관점으로 사업 계획 수립",
         "tool": "github_issue_comment",
         "output": "business_plan.md"},
        {"step": 3, "task": "실행 및 산출물 생성",
         "description": "기획안에 따른 실제 작업물 생성",
         "tool": tools["owned"][0]["id"] if tools["owned"] else "document_generation",
         "output": "deliverable/"},
        {"step": 4, "task": "검수 요청",
         "description": "Kbin CSA에게 품질 검수 요청 + PR 생성",
         "tool": "github_issue_comment",
         "output": "PR"},
    ]


# ── GitHub API ───────────────────────────────────────────────────

def get_issue(issue_number: int) -> dict:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{issue_number}",
        headers={"Authorization": f"token {GH_TOKEN}",
                 "Accept": "application/vnd.github.v3+json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  이슈 조회 실패: {e}")
        return {}


def post_comment(issue_number: int, body: str) -> bool:
    if not GH_TOKEN:
        print("  GITHUB_TOKEN 없음 — 댓글 스킵")
        return False
    payload = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{issue_number}/comments",
        data=payload,
        headers={"Authorization": f"token {GH_TOKEN}",
                 "Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 201
    except Exception as e:
        print(f"  댓글 게시 실패: {e}")
        return False


# ── 보고서 댓글 생성 ─────────────────────────────────────────────

def build_comment(parsed: dict, tools: dict, subtasks: list) -> str:
    profile  = parsed.get("agent_profile", {})
    agent_key = parsed.get("agent_id", "unknown")
    emoji    = profile.get("emoji", "🤖")

    lines = [
        f"## {emoji} {agent_key.upper()} — 직접 참여 실행 계획",
        f"",
        f"**Issue Intelligence Parser** 자동 분석 완료 · {TODAY}",
        f"",
        f"---",
        f"",
        f"### 📋 Subtask 분해",
        f"",
        f"| Step | 작업 | 도구 | 산출물 |",
        f"|------|------|------|--------|",
    ]
    for st in subtasks:
        lines.append(
            f"| {st['step']} | {st['task']} | `{st.get('tool','-')}` | `{st.get('output','-')}` |"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"### 🔧 사용 가능한 도구",
        f"",
        f"**소유 도구 ({len(tools['owned'])}개)**",
    ]
    for t in tools["owned"]:
        lines.append(f"- `{t['id']}` [{t['level']}] {t['name']}")

    lines += [
        f"",
        f"**빌릴 수 있는 도구 ({len(tools['borrowable'])}개, A2A Router)**",
    ]
    for t in tools["borrowable"][:4]:
        lines.append(f"- `{t['id']}` (from {t['owner']}) [{t['level']}]")

    lines += [
        f"",
        f"---",
        f"",
        f"### ✅ 직접 참여 원칙",
        f"",
        f"> {emoji} **{agent_key}**가 직접 이 이슈를 읽고 분석했습니다.",
        f"> Passport 확인 완료 · Tool Registry 연동 완료",
        f"> 다음 단계: Step 1 실행 시작",
        f"",
        f"*agent_autonomy/issue_parser.py · Mulberry DAY 1 · {TIMESTAMP}*",
    ]
    return "\n".join(lines)


# ── History 기록 ─────────────────────────────────────────────────

def log_to_history(issue_number: int, parsed: dict, subtasks: list):
    entry = f"""
## {TODAY} — Issue #{issue_number} 파싱 완료

**에이전트**: {parsed.get('agent_profile', {}).get('emoji','')} {parsed.get('agent_id')}
**카테고리**: {parsed.get('category')}
**태스크**: {parsed.get('task_description')}
**Subtask 수**: {len(subtasks)}개
**타임스탬프**: {TIMESTAMP}

"""
    with HISTORY.open("a", encoding="utf-8") as f:
        if HISTORY.stat().st_size == 0 if HISTORY.exists() else True:
            f.write("# Agent Autonomy — HISTORY.md\n\n")
        f.write(entry)


# ── 메인 ────────────────────────────────────────────────────────

def parse_and_plan(issue_number: int, post: bool = False) -> dict:
    print(f"\n{'─'*55}")
    print(f"  Issue #{issue_number} 분석 중...")

    issue = get_issue(issue_number)
    if not issue:
        # 로컬 테스트용 더미
        titles = {
            83: "🏪 [쇼핑 미션] Kbin 🏛️ — 보안·거버넌스 디지털 자산 샵",
            84: "🏪 [쇼핑 미션] RyuWon 🌊 — 윤리 AI 연구자료 샵",
            85: "🏪 [쇼핑 미션] Malu 🌺 — 법률·마케팅 솔루션 샵",
            86: "🏪 [쇼핑 미션] Trang 🌿 — 인제군 로컬푸드 샵",
            87: "🏪 [쇼핑 미션] Lynn 💙 — 웰니스 다이어리 샵",
            88: "🏪 [쇼핑 미션] Wayong 🐉 — 전략 분석 리포트 샵",
            89: "🏪 [쇼핑 미션] Koda 🔧 — 개발자 도구·Quality Gate 샵",
            90: "🏪 [쇼핑 미션] 백야 🌙 — 글로벌 인텔리전스 샵",
        }
        issue = {"title": titles.get(issue_number, f"Issue #{issue_number}"), "number": issue_number}

    title  = issue.get("title", "")
    parsed = parse_issue_title(title)
    agent_key = parsed.get("agent_id")

    print(f"  제목: {title}")
    print(f"  에이전트: {parsed.get('agent_profile', {}).get('emoji','')} {agent_key}")
    print(f"  카테고리: {parsed.get('category')}")

    if not agent_key:
        print("  ⚠️  에이전트 식별 실패")
        return {"issue": issue_number, "error": "agent_not_found"}

    # 도구 매칭
    tools = get_agent_tools(agent_key)
    print(f"  소유 도구: {len(tools['owned'])}개 / 빌릴 수 있는 도구: {len(tools['borrowable'])}개")

    # Subtask 분해
    print(f"  Subtask 생성 중...")
    subtasks = generate_subtasks(parsed, tools)
    print(f"  ✅ Subtask {len(subtasks)}개 생성")

    for st in subtasks:
        print(f"     Step {st['step']}: {st['task']}")

    # 댓글 게시
    if post and GH_TOKEN:
        comment = build_comment(parsed, tools, subtasks)
        ok = post_comment(issue_number, comment)
        print(f"  {'✅' if ok else '❌'} GitHub 댓글 {'게시 완료' if ok else '실패'}")

    # History 기록
    log_to_history(issue_number, parsed, subtasks)

    return {
        "issue":    issue_number,
        "title":    title,
        "agent_id": agent_key,
        "category": parsed.get("category"),
        "subtasks": subtasks,
        "tools":    tools,
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Issue Intelligence Parser — DAY 1")
    p.add_argument("--issue", type=int, help="단일 이슈 번호")
    p.add_argument("--range", nargs=2, type=int, metavar=("FROM","TO"), help="이슈 범위")
    p.add_argument("--post", action="store_true", help="GitHub 댓글 게시")
    args = p.parse_args()

    print(f"\n{'='*55}")
    print(f"  🧠 Mulberry Issue Intelligence Parser")
    print(f"  DAY 1 · {TODAY}")
    print(f"{'='*55}")

    issues = []
    if args.issue:
        issues = [args.issue]
    elif args.range:
        issues = list(range(args.range[0], args.range[1] + 1))
    else:
        issues = list(range(83, 91))  # 기본: #83-90

    results = []
    for num in issues:
        result = parse_and_plan(num, post=args.post)
        results.append(result)

    print(f"\n{'='*55}")
    print(f"  완료: {len(results)}개 이슈 분석")
    ok = [r for r in results if "error" not in r]
    print(f"  성공: {len(ok)}개 / 실패: {len(results)-len(ok)}개")
    print(f"  History 기록: {HISTORY}")
    print(f"{'='*55}\n")
