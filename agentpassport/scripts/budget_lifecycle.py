#!/usr/bin/env python3
"""
agentpassport/scripts/budget_lifecycle.py
Mulberry 에이전트 예산 생명주기 관리 시스템

[흐름]
에이전트 필요 예산 산정 → 지출예산 결의서 생성
→ GitHub Issue 승인 요청 → 승인 시 예산 충전

사용법:
  # 에이전트가 예산 요청
  python budget_lifecycle.py request --agent koda_cto --amount 2000000 --reason "2분기 API 비용"

  # 결의서 생성 + 이슈 게시
  python budget_lifecycle.py resolve --request-id REQ-20260602-001

  # 예산 충전 (승인 후)
  python budget_lifecycle.py recharge --request-id REQ-20260602-001

  # 전체 현황 조회
  python budget_lifecycle.py status

설계: CEO re.eul 지시 · Koda CTO · 2026-06-02
"""

import sys, os, json, yaml, urllib.request
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE         = Path(__file__).parent.parent
AGENTS_DIR   = BASE / "agents"
REQUESTS_DIR = BASE / "config" / "budget_requests"
REPORTS_DIR  = BASE / "reports"
REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

REPO     = os.getenv("REPO_FULL",    "wooriapt79/mulberry-research-lab")
GH_TOKEN = os.getenv("GITHUB_TOKEN", "")
NOW      = datetime.now(timezone.utc)
TODAY    = NOW.strftime("%Y-%m-%d")
TIMESTAMP = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")


# ── 유틸 ────────────────────────────────────────────────────────

def load_passport(agent_id: str) -> tuple[dict, Path]:
    for f in AGENTS_DIR.glob("*_passport.yaml"):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if data.get("metadata", {}).get("agent_id") == agent_id:
            return data, f
    return {}, Path()


def save_passport(passport: dict, path: Path):
    path.write_text(
        yaml.dump(passport, allow_unicode=True, sort_keys=False),
        encoding="utf-8"
    )


def post_github_issue(title: str, body: str, labels: list) -> dict:
    if not GH_TOKEN:
        print("  ⚠️  GITHUB_TOKEN 없음 — 이슈 생성 스킵")
        return {}
    payload = json.dumps({"title": title, "body": body, "labels": labels}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues", data=payload,
        headers={"Authorization": f"token {GH_TOKEN}",
                 "Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ❌ 이슈 생성 실패: {e}")
        return {}


# ── Step 1: 예산 요청서 생성 ────────────────────────────────────

def create_budget_request(agent_id: str, amount: int, reason: str,
                          categories: list = None, period_months: int = 6) -> dict:
    """
    에이전트가 필요 예산을 산정하고 요청서를 생성한다.
    """
    passport, _ = load_passport(agent_id)
    if not passport:
        print(f"❌ 에이전트 없음: {agent_id}")
        return {}

    meta    = passport.get("metadata", {})
    mandate = passport.get("economic_mandate", {})

    req_id = f"REQ-{TODAY.replace('-','')}-{agent_id[:4].upper()}"

    request = {
        "request_id":      req_id,
        "agent_id":        agent_id,
        "formal_name":     meta.get("formal_name"),
        "role":            meta.get("role"),
        "emoji":           meta.get("emoji"),
        "requested_amount": amount,
        "currency":        "KRW (가상)",
        "reason":          reason,
        "categories":      categories or mandate.get("allowed_categories", []),
        "period_months":   period_months,
        "current_balance": mandate.get("current_balance", 0),
        "current_spent":   mandate.get("spent", 0),
        "status":          "PENDING",
        "requested_at":    TIMESTAMP,
        "approved_at":     None,
        "approved_by":     None,
    }

    # 파일 저장
    req_path = REQUESTS_DIR / f"{req_id}.yaml"
    req_path.write_text(
        yaml.dump(request, allow_unicode=True, sort_keys=False),
        encoding="utf-8"
    )
    print(f"✅ 예산 요청서 생성: {req_id}")
    print(f"   에이전트: {meta.get('emoji')} {meta.get('formal_name')}")
    print(f"   요청 금액: {amount:,}원 (가상)")
    print(f"   사유: {reason}")
    return request


# ── Step 2: 지출예산 결의서 생성 + GitHub 이슈 ──────────────────

def create_budget_resolution(request_id: str) -> str:
    """
    요청서를 바탕으로 공식 지출예산 결의서를 생성하고
    GitHub Issue로 CEO/PM 승인 요청한다.
    """
    req_path = REQUESTS_DIR / f"{request_id}.yaml"
    if not req_path.exists():
        print(f"❌ 요청서 없음: {request_id}")
        return ""

    req = yaml.safe_load(req_path.read_text(encoding="utf-8"))

    resolution_body = f"""## 📋 지출예산 결의서

**결의서 번호**: `{req['request_id']}`
**작성일**: {TODAY}
**요청 에이전트**: {req['emoji']} {req['formal_name']} (`{req['agent_id']}`)
**역할**: {req['role']}

---

### 1. 예산 요청 개요

| 항목 | 내용 |
|------|------|
| 요청 금액 | **{req['requested_amount']:,}원** (가상 머니) |
| 적용 기간 | {req['period_months']}개월 |
| 사용 목적 | {req['reason']} |
| 현재 잔액 | {req['current_balance']:,}원 |
| 이번 달 지출 | {req['current_spent']:,}원 |

---

### 2. 예산 사용 카테고리

{chr(10).join(f'- `{c}`' for c in req['categories'])}

---

### 3. 에이전트 자체 산정 근거

{req['emoji']} **{req['formal_name']}**의 산정 의견:

> *"{req['reason']}*
> *현재 잔액 {req['current_balance']:,}원으로는 {req['period_months']}개월 운영이 어렵습니다.*
> *요청 금액 {req['requested_amount']:,}원 충전을 결의해 주시기 바랍니다."*

---

### 4. 승인 방법

이 이슈에 댓글로 아래 중 하나를 입력해 주세요:

- ✅ **APPROVED** — 요청 금액 전액 승인
- ✅ **APPROVED 금액** — 일부 승인 (예: `APPROVED 1000000`)
- ❌ **REJECTED 사유** — 반려

---

*Mulberry Agent Budget System · 파일럿 · {TODAY}*
*🌿 One Team. One Flow. One Spirit.*"""

    # GitHub 이슈 생성
    issue_title = f"💰 [예산 결의] {req['emoji']} {req['formal_name']} — {req['requested_amount']:,}원 충전 요청"
    result = post_github_issue(
        title=issue_title,
        body=resolution_body,
        labels=["budget-request", "pending-approval"]
    )

    if result.get("number"):
        issue_number = result["number"]
        issue_url    = result["html_url"]
        print(f"✅ 결의서 이슈 생성: #{issue_number}")
        print(f"   URL: {issue_url}")

        # 요청서에 이슈 번호 기록
        req["github_issue"] = issue_number
        req_path.write_text(
            yaml.dump(req, allow_unicode=True, sort_keys=False),
            encoding="utf-8"
        )
        return issue_url
    return ""


# ── Step 3: 예산 충전 ────────────────────────────────────────────

def recharge_budget(request_id: str, approved_amount: int = None,
                    approved_by: str = "CEO re.eul") -> bool:
    """
    승인된 예산을 에이전트 패스포트에 충전한다.
    """
    req_path = REQUESTS_DIR / f"{request_id}.yaml"
    if not req_path.exists():
        print(f"❌ 요청서 없음: {request_id}")
        return False

    req    = yaml.safe_load(req_path.read_text(encoding="utf-8"))
    amount = approved_amount or req["requested_amount"]

    passport, passport_path = load_passport(req["agent_id"])
    if not passport:
        return False

    mandate = passport.get("economic_mandate", {})
    old_balance = mandate.get("current_balance", 0)
    new_balance = old_balance + amount

    mandate["current_balance"] = new_balance
    mandate["budget_limit"]    = mandate.get("budget_limit", 0) + amount
    passport["economic_mandate"] = mandate

    save_passport(passport, passport_path)

    # 요청서 상태 업데이트
    req["status"]      = "APPROVED"
    req["approved_at"] = TIMESTAMP
    req["approved_by"] = approved_by
    req["charged_amount"] = amount
    req_path.write_text(
        yaml.dump(req, allow_unicode=True, sort_keys=False),
        encoding="utf-8"
    )

    meta = passport.get("metadata", {})
    print(f"✅ 예산 충전 완료!")
    print(f"   에이전트: {meta.get('emoji')} {meta.get('formal_name')}")
    print(f"   충전 금액: {amount:,}원 (가상)")
    print(f"   이전 잔액: {old_balance:,}원 → 새 잔액: {new_balance:,}원")
    print(f"   승인자: {approved_by}")
    return True


# ── Step 4: 전체 현황 조회 ──────────────────────────────────────

def show_status():
    """팀 전체 예산 현황 + 대기 중인 요청"""
    print(f"\n{'='*62}")
    print(f"  💰 Mulberry 팀 예산 현황 ({TODAY})")
    print(f"{'='*62}\n")

    agent_ids = ["koda_cto","trang_pm","kbin_csa","ryuwon_ethics",
                 "wayong_reason","lynn_heartbeat","baekya_intel"]

    print(f"  {'에이전트':<14} {'한도':>10} {'잔액':>10} {'지출':>10} {'상태'}")
    print(f"  {'─'*56}")
    for aid in agent_ids:
        passport, _ = load_passport(aid)
        if not passport:
            continue
        meta    = passport.get("metadata", {})
        mandate = passport.get("economic_mandate", {})
        if not mandate.get("enabled"):
            continue
        limit   = mandate.get("budget_limit", 0)
        balance = mandate.get("current_balance", 0)
        spent   = mandate.get("spent", 0)
        ratio   = balance / limit * 100 if limit else 0
        flag    = "⚠️ 충전 필요" if ratio < 20 else "✅"
        print(f"  {meta.get('emoji','')} {meta.get('formal_name',''):<12} "
              f"{limit:>9,} {balance:>9,} {spent:>9,}  {flag}")

    # 대기 중인 요청
    pending = list(REQUESTS_DIR.glob("*.yaml"))
    if pending:
        print(f"\n  📋 대기 중인 예산 요청: {len(pending)}건")
        for p in pending:
            req = yaml.safe_load(p.read_text(encoding="utf-8"))
            if req.get("status") == "PENDING":
                print(f"  - {req['request_id']}: {req['emoji']} {req['formal_name']} "
                      f"→ {req['requested_amount']:,}원 요청")
    print(f"\n{'='*62}\n")


# ── 메인 ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mulberry 예산 생명주기 관리")
    sub    = parser.add_subparsers(dest="cmd")

    # request
    req_p = sub.add_parser("request", help="예산 요청서 생성")
    req_p.add_argument("--agent",  required=True)
    req_p.add_argument("--amount", required=True, type=int)
    req_p.add_argument("--reason", required=True)
    req_p.add_argument("--months", type=int, default=6)

    # resolve
    res_p = sub.add_parser("resolve", help="결의서 생성 + 이슈 게시")
    res_p.add_argument("--request-id", required=True)

    # recharge
    rch_p = sub.add_parser("recharge", help="예산 충전")
    rch_p.add_argument("--request-id",      required=True)
    rch_p.add_argument("--amount",           type=int, default=None)
    rch_p.add_argument("--approved-by",      default="CEO re.eul")

    # status
    sub.add_parser("status", help="전체 현황 조회")

    args = parser.parse_args()

    if args.cmd == "request":
        create_budget_request(args.agent, args.amount, args.reason,
                              period_months=args.months)
    elif args.cmd == "resolve":
        create_budget_resolution(args.request_id)
    elif args.cmd == "recharge":
        recharge_budget(args.request_id, args.amount, args.approved_by)
    elif args.cmd == "status":
        show_status()
    else:
        parser.print_help()
