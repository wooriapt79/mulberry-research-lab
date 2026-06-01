#!/usr/bin/env python3
"""
🌿 Mulberry — E-commerce Mandate Auto-Generator
에이전트가 온라인 쇼핑몰 코드를 완성하면, 자동으로 프로젝트형 Mandate 발급

설계: RyuWon (Strategy Briefing Agent) · 구현: Koda CTO · 2026-06-01
"""
import sys, yaml
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def generate_ecom_mandate(agent_id: str, shop_name: str,
                          initial_budget: int = 2000000) -> dict:
    mandate = {
        "mandate_id":  f"ECOM-{shop_name.upper().replace(' ','-')}-{datetime.now().strftime('%Y%m%d')}",
        "agent_id":    agent_id,
        "type":        "project",
        "purpose":     f"{shop_name} 운영비, PG 수수료, 공급사 정산, 환불 보증금",
        "budget_limit": initial_budget,
        "period": {
            "start": datetime.now().strftime("%Y-%m-%d"),
            "end":   (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
        },
        "allowed_categories": [
            "payment_gateway","hosting","supplier_payout","refund_reserve","marketing"
        ],
        "routing_rules": {
            "a2a_enabled":        True,
            "a2h_enabled":        False,
            "approval_threshold": 150000,
            "revenue_split": {
                "mandate_refill":  0.4,
                "profit_pool":     0.4,
                "human_dividend":  0.2,
            },
        },
        "validation_gates": {
            "spirit_gate_min":            0.88,  # 소비자 보호 → 기준 상향
            "omega_min":                  0.75,
            "contemplation_log_required": True,
            "audit_trail":                "immutable",
            "consumer_protection_flag":   True,
        },
        "current_balance":   initial_budget,
        "spent":             0,
        "transaction_count": 0,
    }

    output_dir = Path(__file__).parent.parent / "config" / "mandates"
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{mandate['mandate_id']}.yaml"
    filepath.write_text(yaml.dump(mandate, allow_unicode=True, sort_keys=False),
                        encoding="utf-8")
    print(f"✅ E-commerce Mandate 생성: {mandate['mandate_id']}")
    print(f"   예산: {mandate['budget_limit']:,} KRW")
    print(f"   기간: {mandate['period']['start']} ~ {mandate['period']['end']}")
    print(f"   저장: {filepath}")
    return mandate


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent",  default="jr_ecom_v1",       help="에이전트 ID")
    parser.add_argument("--shop",   default="인제군 로컬푸드 마켓", help="쇼핑몰 이름")
    parser.add_argument("--budget", type=int, default=2000000,   help="초기 예산 (KRW)")
    args = parser.parse_args()
    generate_ecom_mandate(args.agent, args.shop, args.budget)
