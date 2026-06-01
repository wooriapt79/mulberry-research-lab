#!/usr/bin/env python3
"""
agentpassport/scripts/expense_report.py
Mulberry 팀 월간 지출 보고서 생성기 (파일럿)

사용법:
  python expense_report.py               # 전체 팀 보고서
  python expense_report.py --agent koda  # 특정 에이전트
  python expense_report.py --simulate    # 가상 지출 시뮬레이션 후 보고

설계: 파일럿 가상 머니 개념 / Koda CTO · 2026-06-02
"""

import sys, yaml, json, random
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE        = Path(__file__).parent.parent
AGENTS_DIR  = BASE / "agents"
REPORTS_DIR = BASE / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
TODAY     = datetime.now().strftime("%Y-%m-%d")

# ── 파일럿 가상 지출 시뮬레이션 데이터 ───────────────────────
PILOT_TRANSACTIONS = {
    "koda_cto": [
        {"amount": 89000,  "category": "cloud_infrastructure", "purpose": "Railway 서버 비용", "merchant": "mulberry_internal"},
        {"amount": 45000,  "category": "data_api_usage",        "purpose": "Anthropic API 사용료", "merchant": "mulberry_internal"},
        {"amount": 120000, "category": "cloud_infrastructure", "purpose": "GitHub Actions 추가 크레딧", "merchant": "mulberry_internal"},
    ],
    "trang_pm": [
        {"amount": 30000, "category": "data_api_usage",    "purpose": "Gemini API (Malu 호출)", "merchant": "mulberry_internal"},
        {"amount": 55000, "category": "partner_compensation", "purpose": "외부 디자인 도구 구독", "merchant": "mulberry_internal"},
    ],
    "kbin_csa": [
        {"amount": 25000, "category": "data_api_usage", "purpose": "보안 스캔 API", "merchant": "mulberry_internal"},
    ],
    "ryuwon_ethics": [
        {"amount": 15000, "category": "data_api_usage", "purpose": "문서 인출 API 테스트", "merchant": "mulberry_internal"},
    ],
    "wayong_reason": [
        {"amount": 35000, "category": "data_api_usage", "purpose": "DeepSeek 추론 API", "merchant": "mulberry_internal"},
    ],
    "lynn_heartbeat": [
        {"amount": 8000, "category": "cloud_infrastructure", "purpose": "하트비트 서버 유지", "merchant": "mulberry_internal"},
    ],
    "baekya_intel": [
        {"amount": 20000, "category": "data_api_usage", "purpose": "intel.search_global 실행", "merchant": "mulberry_internal"},
        {"amount": 12000, "category": "cloud_infrastructure", "purpose": "sandbox.execute_code 실행", "merchant": "mulberry_internal"},
    ],
}


def load_passport(agent_id: str) -> dict:
    for f in AGENTS_DIR.glob("*_passport.yaml"):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        if data.get("metadata", {}).get("agent_id") == agent_id:
            return data
    return {}


def simulate_transactions(passport: dict) -> dict:
    """파일럿: 가상 거래 내역을 패스포트에 반영"""
    agent_id = passport.get("metadata", {}).get("agent_id", "")
    mandate  = passport.get("economic_mandate", {})
    if not mandate.get("enabled"):
        return passport

    transactions = PILOT_TRANSACTIONS.get(agent_id, [])
    total_spent  = sum(t["amount"] for t in transactions)

    mandate["spent"]             = total_spent
    mandate["transaction_count"] = len(transactions)
    mandate["current_balance"]   = mandate["budget_limit"] - total_spent
    mandate["_pilot_transactions"] = transactions
    passport["economic_mandate"]   = mandate
    return passport


def calc_omega(mandate: dict) -> float:
    budget_limit = mandate.get("budget_limit", 1)
    spent        = mandate.get("spent", 0)
    utilization  = spent / budget_limit if budget_limit else 0
    efficiency   = 0.9 if utilization < 0.5 else 0.75
    transparency = 1.0 if mandate.get("validation_gates", {}).get("audit_trail") == "immutable" else 0.8
    return round(0.4 * efficiency + 0.3 * 0.95 + 0.3 * transparency, 3)


def generate_agent_report(passport: dict) -> dict:
    meta     = passport.get("metadata", {})
    mandate  = passport.get("economic_mandate", {})
    if not mandate.get("enabled"):
        return None

    transactions = mandate.pop("_pilot_transactions", [])
    budget       = mandate.get("budget_limit", 0)
    spent        = mandate.get("spent", 0)
    remaining    = mandate.get("current_balance", budget)
    utilization  = round(spent / budget * 100, 1) if budget else 0
    omega        = calc_omega(mandate)

    return {
        "agent_id":    meta.get("agent_id"),
        "formal_name": meta.get("formal_name"),
        "emoji":       meta.get("emoji"),
        "role":        meta.get("role"),
        "mandate": {
            "type":       mandate.get("type"),
            "purpose":    mandate.get("purpose"),
            "period":     mandate.get("period"),
            "budget":     budget,
            "spent":      spent,
            "remaining":  remaining,
            "utilization": f"{utilization}%",
        },
        "transactions":     transactions,
        "omega_economy":    omega,
        "spirit_gate_min":  mandate.get("validation_gates", {}).get("spirit_gate_min"),
        "approval_threshold": mandate.get("routing_rules", {}).get("approval_threshold"),
    }


def print_team_report(reports: list):
    total_budget = sum(r["mandate"]["budget"]    for r in reports)
    total_spent  = sum(r["mandate"]["spent"]     for r in reports)
    total_remain = sum(r["mandate"]["remaining"] for r in reports)
    avg_omega    = round(sum(r["omega_economy"]  for r in reports) / len(reports), 3)

    print(f"\n{'='*62}")
    print(f"  🌿 Mulberry 팀 월간 지출 보고서 (파일럿)")
    print(f"  기준일: {TODAY} | 가상 머니 시뮬레이션")
    print(f"{'='*62}\n")

    print(f"  {'에이전트':<12} {'예산':>10} {'지출':>10} {'잔액':>10} {'사용률':>7} {'ω':>6}")
    print(f"  {'─'*58}")

    for r in reports:
        m    = r["mandate"]
        flag = "⚠️" if float(m["utilization"].rstrip("%")) > 70 else " "
        print(f"  {r['emoji']} {r['formal_name']:<10} "
              f"{m['budget']:>9,} "
              f"{m['spent']:>9,} "
              f"{m['remaining']:>9,} "
              f"{m['utilization']:>7} "
              f"{r['omega_economy']:>5} {flag}")

    print(f"  {'─'*58}")
    util_pct = round(total_spent / total_budget * 100, 1) if total_budget else 0
    print(f"  {'합계':<12} {total_budget:>9,} {total_spent:>9,} {total_remain:>9,} {util_pct:>6}%")
    print(f"\n  팀 평균 ω_economy: {avg_omega}")
    print(f"{'='*62}\n")


def save_report(reports: list):
    output = {
        "report_type":  "pilot_monthly_expense",
        "generated_at": TIMESTAMP,
        "period":       TODAY[:7],
        "note":         "파일럿 가상 머니 시뮬레이션",
        "agents":       reports,
        "summary": {
            "total_budget": sum(r["mandate"]["budget"]    for r in reports),
            "total_spent":  sum(r["mandate"]["spent"]     for r in reports),
            "total_remain": sum(r["mandate"]["remaining"] for r in reports),
            "avg_omega":    round(sum(r["omega_economy"]  for r in reports) / len(reports), 3),
        },
    }
    path = REPORTS_DIR / f"expense_report_{TODAY[:7]}_pilot.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  📄 보고서 저장: {path}\n")
    return path


# ── 메인 ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Mulberry 지출 보고서 (파일럿)")
    parser.add_argument("--agent",    help="특정 에이전트 ID")
    parser.add_argument("--simulate", action="store_true", default=True,
                        help="가상 지출 시뮬레이션 (기본값)")
    args = parser.parse_args()

    reports = []
    agent_ids = (
        [args.agent] if args.agent
        else ["koda_cto","trang_pm","kbin_csa","ryuwon_ethics",
              "wayong_reason","lynn_heartbeat","baekya_intel"]
    )

    for agent_id in agent_ids:
        passport = load_passport(agent_id)
        if not passport:
            continue
        if args.simulate:
            passport = simulate_transactions(passport)
        report = generate_agent_report(passport)
        if report:
            reports.append(report)

    if reports:
        print_team_report(reports)
        save_report(reports)
