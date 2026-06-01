#!/usr/bin/env python3
"""
agentpassport/payment/payment_adapter.py
Mulberry 결제 모듈 — PaymentAdapter

[구조]
PaymentAdapter (추상 인터페이스)
    ├── KoreanPGAdapter    (KCP / Toss / Inicis)
    ├── GlobalPGAdapter    (Stripe / PayPal)
    └── A2ALedgerAdapter   (에이전트 간 내부 정산)

[현재 구현 상태]
- 인터페이스 + Stub 구현 (실제 PG 연동은 계약 체결 후 활성화)
- Mandate 잔액 자동 차감 연동
- 거래 내역 financial_audit_logs 기록

[법적 처리]
- 실제 PG 계약: Malu(AI) 검토 → 계약 체결 시점 처리
- 현재: 모든 결제는 A2ALedgerAdapter(내부 정산) 또는 stub 모드

설계: RyuWon (자율경제) · 구현: Koda CTO · 2026-06-02
"""

import sys, os, json, hashlib, yaml
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE      = Path(__file__).parent.parent
AUDIT_DIR = BASE.parent / "mulberry_memory_bank" / "financial_audit_logs"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

TIMESTAMP = lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── 결과 데이터 클래스 ───────────────────────────────────────────

@dataclass
class PaymentResult:
    success:          bool
    transaction_hash: str = ""
    amount:           int = 0
    currency:         str = "KRW"
    adapter_used:     str = ""
    status:           str = ""   # SUCCESS / FAILED / PENDING / STUB
    error_message:    str = ""
    receipt_url:      str = ""
    timestamp:        str = ""
    mandate_charged:  bool = False
    remaining_balance: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# ── 추상 인터페이스 ──────────────────────────────────────────────

class PaymentAdapter(ABC):
    """
    Mulberry 결제 어댑터 추상 인터페이스.
    모든 PG는 이 인터페이스를 구현한다.
    """

    @abstractmethod
    def validate_merchant(self, merchant_id: str) -> bool:
        """가맹점 유효성 검증"""

    @abstractmethod
    def execute(self, mandate_id: str, amount: int,
                purpose: str, metadata: dict) -> PaymentResult:
        """결제 실행"""

    @abstractmethod
    def refund(self, transaction_hash: str,
               reason: str) -> PaymentResult:
        """환불 처리"""

    def _generate_tx_hash(self, mandate_id: str, amount: int) -> str:
        raw = f"{mandate_id}:{amount}:{TIMESTAMP()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:20]

    def _audit_log(self, result: PaymentResult, mandate_id: str,
                   purpose: str, agent_id: str = ""):
        """financial_audit_logs 기록"""
        entry = {
            **result.to_dict(),
            "mandate_id": mandate_id,
            "purpose":    purpose,
            "agent_id":   agent_id,
            "logged_at":  TIMESTAMP(),
        }
        log_file = AUDIT_DIR / f"transactions_{datetime.now().strftime('%Y-%m')}.jsonl"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── A2A 내부 정산 어댑터 (현재 기본 사용) ───────────────────────

class A2ALedgerAdapter(PaymentAdapter):
    """
    Mulberry 내부 정산 레이어.
    에이전트 간 보상·데이터 구매·내부 거래에 사용.
    실제 PG 계약 없이 즉시 사용 가능.
    """

    def validate_merchant(self, merchant_id: str) -> bool:
        return merchant_id in [
            "mulberry_internal", "koda", "kbin", "ryuwon",
            "malu", "trang", "lynn", "wayong", "baekya"
        ]

    def execute(self, mandate_id: str, amount: int,
                purpose: str, metadata: dict = None) -> PaymentResult:
        merchant = (metadata or {}).get("merchant", "mulberry_internal")

        if not self.validate_merchant(merchant):
            return PaymentResult(
                success=False, status="FAILED",
                error_message=f"미등록 가맹점: {merchant}",
                timestamp=TIMESTAMP()
            )

        tx_hash = self._generate_tx_hash(mandate_id, amount)
        result  = PaymentResult(
            success=True,
            transaction_hash=tx_hash,
            amount=amount,
            adapter_used="A2ALedgerAdapter",
            status="SUCCESS",
            receipt_url=f"mulberry://ledger/{tx_hash}",
            timestamp=TIMESTAMP(),
        )
        self._audit_log(result, mandate_id, purpose,
                        (metadata or {}).get("agent_id", ""))
        return result

    def refund(self, transaction_hash: str, reason: str) -> PaymentResult:
        refund_hash = self._generate_tx_hash(transaction_hash, 0)
        return PaymentResult(
            success=True,
            transaction_hash=refund_hash,
            adapter_used="A2ALedgerAdapter",
            status="REFUNDED",
            timestamp=TIMESTAMP()
        )


# ── KCP·Toss·Inicis 한국 PG 어댑터 (Stub — 계약 후 활성화) ─────

class KoreanPGAdapter(PaymentAdapter):
    """
    한국 PG사 연동 어댑터.
    KCP / Toss Payments / Inicis

    [현재 상태]: STUB 모드
    [활성화 조건]: PG사와 계약 체결 + Malu 법적 검토 완료
    [필요 정보]: 사업자등록번호, 통장사본, PG 가맹점 ID
    """

    def __init__(self, pg_name: str = "toss",
                 merchant_id: str = "", secret_key: str = ""):
        self.pg_name     = pg_name
        self.merchant_id = merchant_id or os.getenv("PG_MERCHANT_ID", "")
        self.secret_key  = secret_key  or os.getenv("PG_SECRET_KEY", "")
        self.stub_mode   = not (self.merchant_id and self.secret_key)

        if self.stub_mode:
            print(f"  ⚠️  {pg_name} STUB 모드 — 실제 결제 미처리")
            print(f"     활성화: PG 계약 체결 후 PG_MERCHANT_ID + PG_SECRET_KEY 등록")

    def validate_merchant(self, merchant_id: str) -> bool:
        return bool(self.merchant_id)

    def execute(self, mandate_id: str, amount: int,
                purpose: str, metadata: dict = None) -> PaymentResult:
        if self.stub_mode:
            tx_hash = self._generate_tx_hash(mandate_id, amount)
            result = PaymentResult(
                success=True,
                transaction_hash=tx_hash,
                amount=amount,
                adapter_used=f"KoreanPGAdapter({self.pg_name})[STUB]",
                status="STUB",
                receipt_url=f"https://{self.pg_name}.io/stub/{tx_hash}",
                timestamp=TIMESTAMP(),
            )
            self._audit_log(result, mandate_id, purpose)
            return result

        # 실제 PG 연동 (계약 후 구현)
        # TODO: self.pg_name에 따라 KCP/Toss/Inicis API 호출
        raise NotImplementedError(f"{self.pg_name} 실제 연동 미구현 — 계약 후 개발")

    def refund(self, transaction_hash: str, reason: str) -> PaymentResult:
        if self.stub_mode:
            return PaymentResult(
                success=True, transaction_hash=transaction_hash,
                adapter_used=f"KoreanPGAdapter({self.pg_name})[STUB]",
                status="STUB_REFUNDED", timestamp=TIMESTAMP()
            )
        raise NotImplementedError("환불 — 계약 후 구현")


# ── Stripe 글로벌 어댑터 (Stub) ──────────────────────────────────

class GlobalPGAdapter(PaymentAdapter):
    """
    글로벌 PG 어댑터 (Stripe / PayPal / Adyen).
    [현재 상태]: STUB 모드
    [필요]: STRIPE_SECRET_KEY 등록
    """

    def __init__(self):
        self.stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.stub_mode  = not self.stripe_key
        if self.stub_mode:
            print("  ⚠️  Stripe STUB 모드 — STRIPE_SECRET_KEY 미등록")

    def validate_merchant(self, merchant_id: str) -> bool:
        return bool(self.stripe_key)

    def execute(self, mandate_id: str, amount: int,
                purpose: str, metadata: dict = None) -> PaymentResult:
        if self.stub_mode:
            tx_hash = self._generate_tx_hash(mandate_id, amount)
            return PaymentResult(
                success=True, transaction_hash=tx_hash, amount=amount,
                adapter_used="GlobalPGAdapter(Stripe)[STUB]",
                status="STUB", timestamp=TIMESTAMP()
            )
        raise NotImplementedError("Stripe 실제 연동 — 계약 후 구현")

    def refund(self, transaction_hash: str, reason: str) -> PaymentResult:
        return PaymentResult(
            success=True, transaction_hash=transaction_hash,
            status="STUB_REFUNDED", timestamp=TIMESTAMP()
        )


# ── 결제 라우터 — Mandate 연동 ───────────────────────────────────

class PaymentRouter:
    """
    Passport + Mandate + PaymentAdapter 통합 라우터.
    에이전트의 Mandate 잔액을 확인하고
    적절한 어댑터로 결제를 라우팅한다.
    """

    ADAPTERS = {
        "a2a":    A2ALedgerAdapter,
        "toss":   lambda: KoreanPGAdapter("toss"),
        "kcp":    lambda: KoreanPGAdapter("kcp"),
        "inicis": lambda: KoreanPGAdapter("inicis"),
        "stripe": GlobalPGAdapter,
    }

    def __init__(self, passport_path: Path):
        self.passport = yaml.safe_load(
            passport_path.read_text(encoding="utf-8")
        ) or {}
        self.mandate  = self.passport.get("economic_mandate", {})
        self.agent_id = self.passport.get("metadata", {}).get("agent_id", "")

    def _check_mandate(self, amount: int) -> tuple[bool, str]:
        if not self.mandate.get("enabled"):
            return False, "Mandate 비활성화"
        balance = self.mandate.get("current_balance", 0)
        if amount > balance:
            return False, f"잔액 부족: {balance:,}원 < {amount:,}원"
        threshold = self.mandate.get("routing_rules", {}).get(
            "approval_threshold", 100000)
        if amount > threshold:
            return False, f"승인 임계값 초과: {amount:,}원 > {threshold:,}원 → 스튜어드 승인 필요"
        return True, "OK"

    def _deduct_mandate(self, amount: int, tx_hash: str,
                        passport_path: Path):
        """결제 완료 후 Mandate 잔액 차감"""
        self.mandate["spent"] = self.mandate.get("spent", 0) + amount
        self.mandate["current_balance"] -= amount
        self.mandate["transaction_count"] = \
            self.mandate.get("transaction_count", 0) + 1
        self.passport["economic_mandate"] = self.mandate
        passport_path.write_text(
            yaml.dump(self.passport, allow_unicode=True, sort_keys=False),
            encoding="utf-8"
        )

    def pay(self, amount: int, purpose: str,
            adapter_name: str = "a2a",
            merchant: str = "mulberry_internal",
            passport_path: Path = None) -> PaymentResult:
        """
        결제 메인 엔트리포인트.
        Mandate 검증 → 어댑터 선택 → 결제 실행 → 잔액 차감
        """
        print(f"\n  💳 결제 요청: {amount:,}원 / {purpose}")

        # 1. Mandate 검증
        ok, msg = self._check_mandate(amount)
        if not ok:
            print(f"  ❌ Mandate 거부: {msg}")
            return PaymentResult(
                success=False, status="MANDATE_REJECTED",
                error_message=msg, timestamp=TIMESTAMP()
            )

        # 2. 어댑터 선택
        adapter_cls = self.ADAPTERS.get(adapter_name, A2ALedgerAdapter)
        adapter = adapter_cls() if callable(adapter_cls) else adapter_cls

        # 3. 결제 실행
        mandate_id = self.mandate.get("id", f"MANDATE-{self.agent_id}")
        result = adapter.execute(
            mandate_id=mandate_id,
            amount=amount,
            purpose=purpose,
            metadata={"merchant": merchant, "agent_id": self.agent_id}
        )

        # 4. 성공 시 Mandate 잔액 차감
        if result.success and passport_path:
            self._deduct_mandate(amount, result.transaction_hash, passport_path)
            result.mandate_charged   = True
            result.remaining_balance = self.mandate["current_balance"]
            print(f"  ✅ 결제 완료: {result.transaction_hash}")
            print(f"     잔액: {result.remaining_balance:,}원")

        return result
