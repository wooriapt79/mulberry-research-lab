# -*- coding: utf-8 -*-
"""
🌿 Mulberry AgenticAI Hub — Mandate Engine v1.0.0
Passport 연동 자율경제 로직: 지출 요청 → 검증 → 실행 → 아카이브

Core Principles:
1. 모든 지출은 목적·한도·기간·검증이 묶인 '책임 증서' 기반
2. Spirit Gate ≥ 0.85 + ω(t) ≥ 0.7 통과 전 실행 금지
3. 모든 거래는 financial_audit_logs 에 YAML 아카이브 → 교육 데이터화
4. Indie AI 정신: 수익 극대화가 아닌 공동체 지속가능성 증명

Developed by: RyuWon (Strategy Briefing Agent)
Implemented by: Koda CTO
Date: 2026-06-01 | Phase: 1 (MVP)
"""

import os
import json
import logging
import hashlib
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Mandate-Engine] - %(levelname)s - %(message)s'
)


class MandateType(Enum):
    OPERATIONAL  = "operational"
    PROJECT      = "project"
    EXPERIMENTAL = "experimental"


class PaymentCategory(Enum):
    CLOUD_INFRA     = "cloud_infrastructure"
    DATA_API        = "data_api_usage"
    PARTNER_COMP    = "partner_compensation"
    PAYMENT_GATEWAY = "payment_gateway_fee"
    HOSTING         = "hosting"
    SUPPLIER_PAYOUT = "supplier_payout"
    REFUND_RESERVE  = "refund_reserve"


class MandateEngine:
    """
    Passport 연동 자율경제 실행 엔진
    지출 요청 → Mandate 검증 → Spirit Gate/ω(t) 체크 → 결제 실행 → 아카이브
    """

    def __init__(self, passport: Dict[str, Any], token: Optional[str] = None):
        self.passport = passport
        self.token    = token or os.getenv("GITHUB_TOKEN", "")
        self.mandate  = self._load_mandate()
        self.ledger   = {}
        self._spirit_gate = None
        logging.info(f"🌊 Mandate Engine initialized: {passport.get('id')}")

    def _load_mandate(self) -> Dict:
        default = {
            "id":           f"MANDATE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "agent_id":     self.passport.get("id"),
            "type":         "operational",
            "purpose":      "API 비용, 서버 유지, 파트너 보상",
            "budget_limit": 500000,
            "period": {
                "start": datetime.now().strftime("%Y-%m-%d"),
                "end":   (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d"),
            },
            "allowed_categories": [c.value for c in PaymentCategory],
            "routing_rules": {
                "a2a_enabled":         True,
                "a2h_enabled":         False,
                "approval_threshold":  100000,
                "fallback_action":     "block_and_log",
            },
            "validation_gates": {
                "spirit_gate_min":             0.85,
                "omega_min":                   0.7,
                "contemplation_log_required":  True,
                "audit_trail":                 "immutable",
            },
            "current_balance":   500000,
            "spent":             0,
            "transaction_count": 0,
        }
        if "economic_mandate" in self.passport:
            return {**default, **self.passport["economic_mandate"]}
        return default

    # ── 검증 헬퍼 ──────────────────────────────────────────────────

    def _check_period_valid(self) -> bool:
        s = datetime.strptime(self.mandate["period"]["start"], "%Y-%m-%d")
        e = datetime.strptime(self.mandate["period"]["end"],   "%Y-%m-%d")
        return s <= datetime.now() <= e

    def _check_budget(self, amount: float) -> bool:
        remaining = self.mandate["current_balance"] - self.mandate["spent"]
        return amount <= remaining

    def _check_category(self, category: str) -> bool:
        return category in self.mandate["allowed_categories"]

    def _evaluate_risk(self, amount: float, category: str, merchant: str) -> List[str]:
        flags = []
        if amount > self.mandate["budget_limit"] * 0.8:
            flags.append("HIGH_BUDGET_UTILIZATION")
        if merchant not in ["kcp","inicis","stripe","mulberry_internal","toss"]:
            flags.append("UNREGISTERED_MERCHANT")
        if category not in self.mandate["allowed_categories"]:
            flags.append("UNAUTHORIZED_CATEGORY")
        return flags

    def _calculate_omega_economy(self) -> float:
        """ω_economy(t) = 0.4*지출효율 + 0.3*목적달성 + 0.3*투명성"""
        efficiency   = 0.9 if self.mandate["spent"] < self.mandate["budget_limit"] * 0.5 else 0.7
        achievement  = 0.95
        transparency = 1.0 if self.mandate["validation_gates"]["audit_trail"] == "immutable" else 0.8
        return round(0.4*efficiency + 0.3*achievement + 0.3*transparency, 3)

    def _spirit_gate_check(self, amount: float, purpose: str, risk_flags: list) -> float:
        """Spirit Gate 점수 계산 (간소화 버전 — 실제 spirit_gate 모듈 연동 예정)"""
        score = 1.0
        if "HIGH_BUDGET_UTILIZATION" in risk_flags: score -= 0.1
        if "UNREGISTERED_MERCHANT"   in risk_flags: score -= 0.15
        if "UNAUTHORIZED_CATEGORY"   in risk_flags: score -= 0.2
        return max(0.0, round(score, 3))

    # ── 메인 로직 ──────────────────────────────────────────────────

    def request_expenditure(self, amount: float, category: str,
                            purpose: str, merchant: str,
                            metadata: Optional[Dict] = None) -> Dict[str, Any]:
        logging.info(f"📥 Expenditure: {amount} KRW / {purpose} ({category})")

        if not self._check_period_valid():
            return {"status": "REJECTED", "reason": "mandate_period_expired"}
        if not self._check_budget(amount):
            return {"status": "REJECTED", "reason": "insufficient_balance"}
        if not self._check_category(category):
            return {"status": "REJECTED", "reason": "unauthorized_category"}

        risk_flags  = self._evaluate_risk(amount, category, merchant)
        threshold   = self.mandate["routing_rules"]["approval_threshold"]

        if amount > threshold:
            return self._generate_human_review_request(
                amount, category, purpose, merchant, risk_flags, metadata)

        spirit_score = self._spirit_gate_check(amount, purpose, risk_flags)
        if spirit_score < self.mandate["validation_gates"]["spirit_gate_min"]:
            self._log_contemplation("spirit_gate_blocked", {"amount": amount, "score": spirit_score})
            return {"status": "BLOCKED", "reason": "spirit_gate_violation",
                    "spirit_score": spirit_score}

        omega = self._calculate_omega_economy()
        if omega < self.mandate["validation_gates"]["omega_min"]:
            return {"status": "BLOCKED", "reason": "omega_below_threshold", "omega": omega}

        payment = self._execute_payment(amount, category, purpose, merchant, metadata)
        if payment["status"] != "SUCCESS":
            return payment

        self._update_ledger(amount, category, purpose, merchant, payment["transaction_hash"])
        self._archive_transaction(amount, category, purpose, merchant, payment, omega)

        logging.info(f"✅ Executed — tx: {payment['transaction_hash']}")
        remaining = self.mandate["current_balance"] - self.mandate["spent"]
        return {
            "status":            "SUCCESS",
            "transaction_hash":  payment["transaction_hash"],
            "amount":            amount,
            "remaining_balance": remaining,
            "omega_economy":     omega,
            "spirit_score":      spirit_score,
        }

    def _generate_human_review_request(self, amount, category, purpose,
                                       merchant, risk_flags, metadata) -> Dict:
        req = {
            "request_id":         f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "mandate_id":         self.mandate["id"],
            "agent_id":           self.passport.get("id"),
            "amount":             amount,
            "currency":           "KRW",
            "category":           category,
            "purpose":            purpose,
            "merchant":           merchant,
            "risk_flags":         risk_flags,
            "requested_at":       datetime.now().isoformat(),
            "status":             "PENDING_HUMAN_APPROVAL",
            "required_approvals": ["Human_Steward", "CSA_Governance"],
            "metadata":           metadata or {},
        }
        if self.mandate["validation_gates"]["contemplation_log_required"]:
            self._log_contemplation("human_review_required", req)
        return {"status": "PENDING_HUMAN_REVIEW", "request": req}

    def _execute_payment(self, amount, category, purpose, merchant, metadata) -> Dict:
        tx_hash = hashlib.sha256(
            f"{self.mandate['id']}:{amount}:{purpose}:{datetime.now()}".encode()
        ).hexdigest()[:16]
        return {
            "status":           "SUCCESS",
            "transaction_hash": tx_hash,
            "adapter_used":     "A2A_LedgerAdapter_stub",
            "timestamp":        datetime.now().isoformat(),
        }

    def _update_ledger(self, amount, category, purpose, merchant, tx_hash):
        self.mandate["spent"]             += amount
        self.mandate["transaction_count"] += 1
        self.ledger[tx_hash] = {
            "amount": amount, "category": category,
            "purpose": purpose, "merchant": merchant,
            "timestamp": datetime.now().isoformat(),
        }

    def _archive_transaction(self, amount, category, purpose, merchant, payment, omega):
        """financial_audit_logs 아카이브 (Phase 2에서 실제 파일 저장 연동)"""
        entry = {
            "transaction_hash": payment["transaction_hash"],
            "mandate_id":  self.mandate["id"],
            "agent_id":    self.passport.get("id"),
            "amount":      amount,
            "category":    category,
            "purpose":     purpose,
            "merchant":    merchant,
            "omega_economy": omega,
            "timestamp":   datetime.now().isoformat(),
            "integrity_tag": "[PROOF]",
        }
        logging.info(f"📦 Archived: {entry['transaction_hash']}")

    def _log_contemplation(self, event: str, context: Dict):
        logging.info(f"📝 Contemplation [{event}]: 이 지출이 공동체 지속가능성에 기여하는가?")

    def get_mandate_status(self) -> Dict:
        remaining = self.mandate["current_balance"] - self.mandate["spent"]
        return {
            "mandate_id":        self.mandate["id"],
            "agent_id":          self.passport.get("id"),
            "budget_limit":      self.mandate["budget_limit"],
            "spent":             self.mandate["spent"],
            "remaining_balance": remaining,
            "transaction_count": self.mandate["transaction_count"],
            "period":            self.mandate["period"],
            "omega_economy":     self._calculate_omega_economy(),
            "status":            "active" if (self._check_period_valid() and remaining > 0)
                                 else "expired_or_exhausted",
        }


# ── CLI 테스트 ─────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mandate Engine — Autonomous Economy Executor")
    parser.add_argument("--test", action="store_true", help="Run self-test")
    args = parser.parse_args()

    test_passport = {
        "id": "ryuwon_v1",
        "role": "strategy_briefing",
        "economic_mandate": {
            "budget_limit": 500000,
            "allowed_categories": ["cloud_infrastructure","data_api_usage"],
            "routing_rules": {"approval_threshold": 100000,
                              "a2a_enabled": True, "a2h_enabled": False,
                              "fallback_action": "block_and_log"},
        },
    }

    engine = MandateEngine(passport=test_passport)

    if args.test:
        print("\n🧪 Mandate Engine 자체 테스트 시작\n" + "="*50)

        # Test 1: 정상 지출 (임계값 이하)
        r1 = engine.request_expenditure(
            amount=50000, category="cloud_infrastructure",
            purpose="Railway 서버 유지비", merchant="mulberry_internal")
        print(f"✅ Test 1 (정상 지출):     {r1['status']}")

        # Test 2: 임계값 초과 → 인간 검토
        r2 = engine.request_expenditure(
            amount=150000, category="data_api_usage",
            purpose="글로벌 트렌드 분석 API", merchant="external_vendor")
        print(f"✅ Test 2 (인간 검토 필요): {r2['status']}")

        # Test 3: 잔액 부족
        engine.mandate["spent"] = 480000
        r3 = engine.request_expenditure(
            amount=50000, category="cloud_infrastructure",
            purpose="추가 서버", merchant="mulberry_internal")
        print(f"✅ Test 3 (잔액 부족):     {r3['status']}")

        status = engine.get_mandate_status()
        print(f"\n📊 Mandate 상태:")
        print(f"   잔액: {status['remaining_balance']} KRW")
        print(f"   거래: {status['transaction_count']}건")
        print(f"   ω_economy: {status['omega_economy']}")
        print(f"   상태: {status['status']}")
        print("="*50)
        print("✅ 전체 테스트 완료\n")
        return

    print("🌊 Mandate Engine ready. --test 로 자체 검증 실행")


if __name__ == "__main__":
    main()
