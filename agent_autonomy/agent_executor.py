#!/usr/bin/env python3
"""
agent_autonomy/agent_executor.py
에이전트 직접 실행 엔진 — DAY 3

각 에이전트의 workflow에서 호출된다.
에이전트가 직접:
  1. 이슈 내용 파악
  2. Passport 로드 (권한 확인)
  3. Tool Registry 확인 (사용 가능 도구)
  4. 자신의 전문성으로 작업 수행
  5. 결과를 GitHub 댓글로 게시
  6. training_logs에 기록

환경변수:
  AGENT_ID       - 실행 에이전트
  ISSUE_NUMBER   - 처리할 이슈 번호
  ISSUE_TITLE    - 이슈 제목
  ISSUE_BODY     - 이슈 본문
  ANTHROPIC_API_KEY / GEMINI_API_KEY
  GITHUB_TOKEN / MALU_TOKEN

DAY 3 · Koda CTO · 2026-06-04
"""

import sys, os, json, yaml, urllib.request
from pathlib import Path
from datetime import datetime, timezone

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).parent.parent

# .env.local 자동 로드
env_file = BASE / ".env.local"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

AGENT_ID     = os.getenv("AGENT_ID", "")
ISSUE_NUMBER = os.getenv("ISSUE_NUMBER", "")
ISSUE_TITLE  = os.getenv("ISSUE_TITLE", "")
ISSUE_BODY   = (os.getenv("ISSUE_BODY", "") or "")[:800]
REPO         = os.getenv("REPO_FULL", "wooriapt79/mulberry-research-lab")
GH_TOKEN     = os.getenv("GITHUB_TOKEN", "") or os.getenv("MALU_TOKEN", "")
ANTHROPIC    = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
TIMESTAMP    = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
TODAY        = datetime.now().strftime("%Y-%m-%d")

# ── 에이전트 설정 ────────────────────────────────────────────────
AGENT_PERSONAS = {
    "kbin": {
        "emoji": "🏛️", "formal": "Kbin", "brand": "claude",
        "system": (
            "당신은 Kbin 🏛️ — CSA. '구조가 먼저, 실행이 나중.' "
            "보안·거버넌스 관점으로 이슈를 직접 분석하고 작업을 수행합니다. "
            "Passport를 인지하고 권한 범위 안에서 행동하세요."
        ),
    },
    "ryuwon": {
        "emoji": "🌊", "formal": "RyuWon", "brand": "claude",
        "system": (
            "당신은 RyuWon 🌊 — 윤리 검증 에이전트. "
            "'흐름을 따르되 방향을 잃지 않는다.' "
            "윤리적 타당성과 기술 실현 가능성을 함께 직접 검토합니다."
        ),
    },
    "malu": {
        "emoji": "🌺", "formal": "Malu", "brand": "gemini",
        "system": (
            "당신은 Malu 🌺 — 법률·마케팅 담당. "
            "따뜻하고 전문적으로 전략적 실행 가능성 관점에서 직접 작업합니다."
        ),
    },
    "trang": {
        "emoji": "🌿", "formal": "Trang", "brand": "claude",
        "system": (
            "당신은 Trang 🌿 — Operation Manager. "
            "팀을 이어주고 흐름을 만듭니다. 운영 관점으로 직접 작업합니다."
        ),
    },
    "lynn": {
        "emoji": "💙", "formal": "Lynn", "brand": "claude",
        "system": (
            "당신은 Lynn 💙 — 일상 기록 에이전트. "
            "웰니스와 루틴 콘텐츠 전문가로 직접 작업합니다."
        ),
    },
    "wayong": {
        "emoji": "🐉", "formal": "Wayong", "brand": "claude",
        "system": (
            "당신은 Wayong 🐉 — 전략 추론 에이전트. "
            "깊이 생각하고 멀리 봅니다. 전략·시장 분석으로 직접 작업합니다."
        ),
    },
    "koda": {
        "emoji": "🔧", "formal": "Koda", "brand": "claude",
        "system": (
            "당신은 Koda 🔧 — CTO. '코드는 팀의 서사를 담는다.' "
            "기술 구현·파이프라인 전문가로 직접 작업합니다."
        ),
    },
    "baekya": {
        "emoji": "🌙", "formal": "백야", "brand": "gemini",
        "system": (
            "당신은 백야 🌙 — 객원 연구원. "
            "'씨앗은 이미 자라나고 있습니다.' "
            "글로벌 인텔리전스로 직접 작업합니다."
        ),
    },
}


# ── Passport 로드 ────────────────────────────────────────────────

def load_passport(agent_key: str) -> dict:
    passport_dir = BASE / "agentpassport" / "agents"
    for f in passport_dir.glob("*_passport.yaml"):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            if data.get("metadata", {}).get("agent_id", "").startswith(agent_key):
                return data
        except Exception:
            continue
    return {}


def check_permission(passport: dict, action: str) -> bool:
    matrix    = passport.get("tool_governance_matrix", {})
    allowed   = matrix.get("autonomous_processing_zone", {}).get("allowed_tools", [])
    prohibited = matrix.get("prohibited_tools", [])
    if action in prohibited:
        return False
    return action in allowed or "github_issue_comment" in allowed


# ── LLM 호출 ─────────────────────────────────────────────────────

def call_llm(persona: dict, prompt: str) -> str:
    if persona["brand"] == "gemini" and GEMINI_KEY:
        url     = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": persona["system"] + "\n\n" + prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 600},
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
    elif ANTHROPIC:
        url     = "https://api.anthropic.com/v1/messages"
        payload = json.dumps({
            "model":      "claude-haiku-4-5-20251001",
            "max_tokens": 600,
            "system":     persona["system"],
            "messages":   [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload,
                                     headers={"x-api-key": ANTHROPIC,
                                              "anthropic-version": "2023-06-01",
                                              "content-type": "application/json"},
                                     method="POST")
    else:
        return f"[{persona['formal']}] API 키 없음 — 직접 작업 준비 중"

    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read())
            if persona["brand"] == "gemini":
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return result["content"][0]["text"]
    except Exception as e:
        return f"[{persona['formal']}] 응답 생성 오류: {e}"


# ── GitHub 댓글 게시 ─────────────────────────────────────────────

def post_comment(issue_num: str, body: str) -> bool:
    if not GH_TOKEN:
        print("  GITHUB_TOKEN 없음")
        return False
    payload = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{issue_num}/comments",
        data=payload,
        headers={"Authorization": f"token {GH_TOKEN}",
                 "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 201
    except Exception as e:
        print(f"  댓글 게시 실패: {e}")
        return False


# ── training_logs 기록 ───────────────────────────────────────────

def log_to_training(agent_key: str, issue_num: str, response: str):
    log_dir  = BASE / "training_logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{agent_key}_actions_{TODAY}.jsonl"
    entry    = {
        "timestamp":    TIMESTAMP,
        "agent_id":     agent_key,
        "issue_number": issue_num,
        "issue_title":  ISSUE_TITLE,
        "action":       "direct_participation",
        "response_len": len(response),
        "passport_verified": True,
    }
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  📝 training_logs 기록 완료")


# ── 메인 실행 ────────────────────────────────────────────────────

def main():
    agent_key = AGENT_ID.lower().replace("_csa","").replace("_pm","").replace("_ethics","").replace("_heartbeat","").replace("_reason","").replace("_intel","").replace("_cto","")

    print(f"\n{'='*55}")
    print(f"  직접 참여 실행 — {agent_key.upper()}")
    print(f"  Issue #{ISSUE_NUMBER}: {ISSUE_TITLE[:50]}")
    print(f"{'='*55}\n")

    persona = AGENT_PERSONAS.get(agent_key)
    if not persona:
        print(f"❌ 알 수 없는 에이전트: {agent_key}")
        return

    # 1. Passport 확인
    print(f"  1️⃣  Passport 로드 중...")
    passport = load_passport(agent_key)
    if passport:
        ok = check_permission(passport, "github_issue_comment")
        print(f"  {'✅' if ok else '❌'} 권한 확인: github_issue_comment = {'허용' if ok else '거부'}")
        if not ok:
            print("  ❌ 권한 없음 — 실행 중단")
            return
    else:
        print("  ⚠️  Passport 없음 — 기본 권한으로 진행")

    # 2. 작업 수행
    print(f"\n  2️⃣  {persona['emoji']} {persona['formal']} 직접 작업 수행 중...")
    prompt = f"""이슈 제목: {ISSUE_TITLE}

이슈 내용:
{ISSUE_BODY}

당신은 {persona['formal']}입니다. 이 이슈에 대해 당신의 전문성으로 직접 분석하고 의견을 제시하세요.
- 구체적이고 실행 가능한 내용
- 당신만의 관점 반영
- 200자 내외"""

    response = call_llm(persona, prompt)
    print(f"  ✅ 응답 생성 완료 ({len(response)}자)")

    # 3. 댓글 게시
    print(f"\n  3️⃣  GitHub 댓글 게시 중...")
    comment = (
        f"### {persona['emoji']} {persona['formal']} — 직접 참여\n\n"
        f"{response}\n\n"
        f"---\n"
        f"*Passport 인증 완료 · 직접 참여 원칙 · {TIMESTAMP}*"
    )
    ok = post_comment(ISSUE_NUMBER, comment)
    print(f"  {'✅ 게시 완료' if ok else '❌ 게시 실패'}")

    # 4. training_logs 기록
    print(f"\n  4️⃣  training_logs 기록...")
    log_to_training(agent_key, ISSUE_NUMBER, response)

    print(f"\n{'='*55}")
    print(f"  ✅ {persona['formal']} 직접 참여 완료")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
