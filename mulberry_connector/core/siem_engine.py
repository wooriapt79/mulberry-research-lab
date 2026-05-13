"""
AI-SIEM Engine — 위협 탐지 · 신뢰도 평가

정의 (Steward AI Standard v0.1):
  Security Information and Event Management for AI.
  Railway 인프라 메트릭 + Spirit Score → 보안 이벤트 생성 → Incident Response.

데이터 흐름:
  RailwayMonitor.snapshot()
    → SiemEngine.analyze(snapshot)
      → [SiemEvent, ...]
        → siem_events.jsonl (감사 로그)
        → execution_audit.jsonl (기존 감사 로그와 통합)
        → GET /v1/siem/events (API 노출)

탐지 규칙:
  R1. 5xx 에러율 급등 (warning: 5%, critical: 15%)
  R2. 응답시간 급등 (warning: 2s, critical: 5s p99)
  R3. 트래픽 스파이크 (기준선 대비 3배 초과)
  R4. Spirit Score 낮은 에이전트 + 에러율 복합 이상
  R5. 비정상 IP 반복 접근 (동일 IP 10회 이상 / 분)

설계: re.eul (개념) · Railway Agent (데이터) · Koda (구현) (2026-05-12)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from adapters.railway_monitor import MetricSnapshot, RailwayMonitor


# ── 설정 ─────────────────────────────────────────────────────────────

SIEM_LOG_PATH = (
    Path(__file__).parent.parent.parent
    / "training_logs"
    / "siem_events.jsonl"
)

# 탐지 임계값
THRESHOLDS = {
    # R1: 5xx 에러율
    "error_5xx_warning":  0.05,   # 5%
    "error_5xx_critical": 0.15,   # 15%
    # R2: 응답시간 (p99, ms)
    "latency_warning_ms":  2_000,
    "latency_critical_ms": 5_000,
    # R3: 트래픽 스파이크 (기준선 대비 배수)
    "traffic_spike_ratio": 3.0,
    # R4: Spirit Score 복합 임계값
    "spirit_low_threshold": 0.75,
    "spirit_error_compound": 0.03,  # Spirit 낮고 에러율 3% 이상
    # R5: 동일 IP 반복 접근 (분당)
    "ip_repeat_threshold": 10,
}


# ── 데이터 모델 ──────────────────────────────────────────────────────

class SiemSeverity(str, Enum):
    INFO     = "info"
    WARNING  = "warning"
    CRITICAL = "critical"


class SiemCategory(str, Enum):
    ERROR_RATE    = "error_rate"       # 5xx/4xx 에러율
    LATENCY       = "latency"          # 응답 지연
    TRAFFIC_SPIKE = "traffic_spike"    # 트래픽 급증
    TRUST_FAILURE = "trust_failure"    # Spirit Score + 에러 복합
    IP_ANOMALY    = "ip_anomaly"       # 비정상 IP 접근
    INFRA_HEALTH  = "infra_health"     # CPU/메모리


@dataclass
class SiemEvent:
    """단일 보안 이벤트."""
    event_id: str
    timestamp: str
    severity: SiemSeverity
    category: SiemCategory
    title: str
    detail: str
    source: str                        # "railway.metrics" | "railway.logs" | ...
    metric_value: float                # 탐지된 지표 값
    threshold_value: float             # 넘어선 임계값
    action_recommended: str            # "monitor" | "human_review" | "block"
    affected_tool: str = ""
    spirit_score: float = 1.0          # 연관 에이전트 Spirit Score (없으면 1.0)
    resolved: bool = False

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        d["category"] = self.category.value
        return d

    @classmethod
    def make(
        cls,
        severity: SiemSeverity,
        category: SiemCategory,
        title: str,
        detail: str,
        source: str,
        metric_value: float,
        threshold_value: float,
        action: str,
        **kwargs,
    ) -> "SiemEvent":
        return cls(
            event_id=f"siem_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            severity=severity,
            category=category,
            title=title,
            detail=detail,
            source=source,
            metric_value=metric_value,
            threshold_value=threshold_value,
            action_recommended=action,
            **kwargs,
        )


# ── 탐지 규칙 ────────────────────────────────────────────────────────

def _rule_error_rate(snap: MetricSnapshot) -> Optional[SiemEvent]:
    """R1: 5xx 에러율 임계값 초과."""
    rate = snap.error_rate_5xx
    if rate >= THRESHOLDS["error_5xx_critical"]:
        return SiemEvent.make(
            severity=SiemSeverity.CRITICAL,
            category=SiemCategory.ERROR_RATE,
            title="🚨 5xx 에러율 임계값 초과 (CRITICAL)",
            detail=(
                f"서비스 에러율 {rate:.1%}이 임계값 "
                f"{THRESHOLDS['error_5xx_critical']:.0%}을 초과했습니다. "
                f"총 요청 {snap.req_count_total}건 중 "
                f"5xx {snap.req_count_5xx}건 발생."
            ),
            source="railway.metrics",
            metric_value=rate,
            threshold_value=THRESHOLDS["error_5xx_critical"],
            action="human_review",
        )
    if rate >= THRESHOLDS["error_5xx_warning"]:
        return SiemEvent.make(
            severity=SiemSeverity.WARNING,
            category=SiemCategory.ERROR_RATE,
            title="⚠️ 5xx 에러율 경고",
            detail=(
                f"서비스 에러율 {rate:.1%}이 경고 임계값 "
                f"{THRESHOLDS['error_5xx_warning']:.0%}을 초과했습니다."
            ),
            source="railway.metrics",
            metric_value=rate,
            threshold_value=THRESHOLDS["error_5xx_warning"],
            action="monitor",
        )
    return None


def _rule_latency(snap: MetricSnapshot) -> Optional[SiemEvent]:
    """R2: p99 응답시간 급등."""
    p99 = snap.latency_p99_ms
    if p99 <= 0:
        return None
    if p99 >= THRESHOLDS["latency_critical_ms"]:
        return SiemEvent.make(
            severity=SiemSeverity.CRITICAL,
            category=SiemCategory.LATENCY,
            title="🚨 응답시간 임계값 초과 (CRITICAL)",
            detail=(
                f"p99 응답시간 {p99:.0f}ms가 임계값 "
                f"{THRESHOLDS['latency_critical_ms']}ms를 초과했습니다. "
                f"DDoS 또는 서비스 과부하 가능성을 확인하세요."
            ),
            source="railway.metrics",
            metric_value=p99,
            threshold_value=THRESHOLDS["latency_critical_ms"],
            action="human_review",
        )
    if p99 >= THRESHOLDS["latency_warning_ms"]:
        return SiemEvent.make(
            severity=SiemSeverity.WARNING,
            category=SiemCategory.LATENCY,
            title="⚠️ 응답시간 경고",
            detail=f"p99 응답시간 {p99:.0f}ms — 경고 수준.",
            source="railway.metrics",
            metric_value=p99,
            threshold_value=THRESHOLDS["latency_warning_ms"],
            action="monitor",
        )
    return None


def _rule_traffic_spike(
    snap: MetricSnapshot,
    baseline: Optional[MetricSnapshot],
) -> Optional[SiemEvent]:
    """R3: 트래픽 스파이크 — 기준선 대비 3배 초과."""
    if baseline is None or baseline.req_count_total == 0:
        return None
    ratio = snap.req_count_total / baseline.req_count_total
    if ratio >= THRESHOLDS["traffic_spike_ratio"]:
        return SiemEvent.make(
            severity=SiemSeverity.WARNING,
            category=SiemCategory.TRAFFIC_SPIKE,
            title="⚠️ 트래픽 스파이크 감지",
            detail=(
                f"현재 요청 수({snap.req_count_total})가 "
                f"기준선({baseline.req_count_total})의 {ratio:.1f}배입니다. "
                f"비정상 트래픽 또는 공격 가능성을 확인하세요."
            ),
            source="railway.logs",
            metric_value=ratio,
            threshold_value=THRESHOLDS["traffic_spike_ratio"],
            action="human_review",
        )
    return None


def _rule_spirit_compound(
    snap: MetricSnapshot,
    agent_spirit_score: float = 1.0,
) -> Optional[SiemEvent]:
    """R4: Spirit Score 낮은 에이전트 + 에러율 복합 이상."""
    low_spirit = agent_spirit_score < THRESHOLDS["spirit_low_threshold"]
    high_error = snap.error_rate_5xx >= THRESHOLDS["spirit_error_compound"]
    if low_spirit and high_error:
        return SiemEvent.make(
            severity=SiemSeverity.CRITICAL,
            category=SiemCategory.TRUST_FAILURE,
            title="🚨 낮은 Spirit Score + 에러율 복합 이상",
            detail=(
                f"Spirit Score {agent_spirit_score:.2f}(기준 "
                f"{THRESHOLDS['spirit_low_threshold']}) 미달 에이전트가 "
                f"에러율 {snap.error_rate_5xx:.1%} 상황에서 도구를 호출 중입니다. "
                "즉시 격리(block_or_quarantine)를 권장합니다."
            ),
            source="railway.metrics+spirit_gate",
            metric_value=snap.error_rate_5xx,
            threshold_value=THRESHOLDS["spirit_error_compound"],
            action="block",
            spirit_score=agent_spirit_score,
        )
    return None


def _rule_ip_anomaly(snap: MetricSnapshot) -> Optional[SiemEvent]:
    """R5: 동일 IP 반복 접근 탐지."""
    ip_counts: dict[str, int] = {}
    for h in snap.recent_http:
        if h.src_ip:
            ip_counts[h.src_ip] = ip_counts.get(h.src_ip, 0) + 1

    suspicious = {
        ip: cnt for ip, cnt in ip_counts.items()
        if cnt >= THRESHOLDS["ip_repeat_threshold"]
    }
    if suspicious:
        top_ip, top_cnt = max(suspicious.items(), key=lambda x: x[1])
        return SiemEvent.make(
            severity=SiemSeverity.WARNING,
            category=SiemCategory.IP_ANOMALY,
            title="⚠️ 비정상 IP 반복 접근 감지",
            detail=(
                f"IP {top_ip}에서 {top_cnt}회 반복 접근이 감지됐습니다. "
                f"총 {len(suspicious)}개 의심 IP 발견."
            ),
            source="railway.logs",
            metric_value=float(top_cnt),
            threshold_value=float(THRESHOLDS["ip_repeat_threshold"]),
            action="monitor",
        )
    return None


# ── SIEM 엔진 ────────────────────────────────────────────────────────

class SiemEngine:
    """
    AI-SIEM 핵심 엔진.

    Mulberry Steward AI Standard v0.1 구현:
      - Railway 메트릭 → 5개 탐지 규칙 적용
      - Spirit Score 연동 (Trust Failure 복합 탐지)
      - 이벤트 → siem_events.jsonl 감사 로그
      - GET /v1/siem/events 엔드포인트용 조회 지원
    """

    def __init__(
        self,
        monitor: Optional[RailwayMonitor] = None,
        log_path: Path = SIEM_LOG_PATH,
    ):
        self.monitor = monitor or RailwayMonitor()
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._events: list[SiemEvent] = []   # 인메모리 최근 이벤트

    # ── 분석 ──────────────────────────────────────────────────────────

    def analyze(
        self,
        snapshot: Optional[MetricSnapshot] = None,
        agent_spirit_score: float = 1.0,
    ) -> list[SiemEvent]:
        """
        메트릭 스냅샷을 5개 규칙으로 분석하여 이벤트 목록 반환.
        snapshot=None이면 monitor.snapshot()을 자동 호출.
        """
        if snapshot is None:
            snapshot = self.monitor.snapshot()

        baseline = self.monitor.get_baseline()
        events: list[SiemEvent] = []

        rules = [
            _rule_error_rate(snapshot),
            _rule_latency(snapshot),
            _rule_traffic_spike(snapshot, baseline),
            _rule_spirit_compound(snapshot, agent_spirit_score),
            _rule_ip_anomaly(snapshot),
        ]
        for ev in rules:
            if ev is not None:
                events.append(ev)
                self._record(ev)

        # 현재 스냅샷을 다음 분석의 기준선으로 업데이트
        self.monitor.update_baseline(snapshot)

        return events

    def run_cycle(self, agent_spirit_score: float = 1.0) -> dict:
        """
        단일 모니터링 사이클 실행.
        Returns: 스냅샷 + 이벤트 요약
        """
        snapshot = self.monitor.snapshot()
        events = self.analyze(snapshot, agent_spirit_score)

        critical = [e for e in events if e.severity == SiemSeverity.CRITICAL]
        warnings  = [e for e in events if e.severity == SiemSeverity.WARNING]

        return {
            "cycle_at": snapshot.collected_at,
            "source_mode": "live" if not snapshot.is_mock else "mock",
            "snapshot": snapshot.to_dict(),
            "events_total": len(events),
            "critical_count": len(critical),
            "warning_count": len(warnings),
            "events": [e.to_dict() for e in events],
            "highest_severity": (
                "critical" if critical
                else "warning" if warnings
                else "ok"
            ),
        }

    # ── 조회 ──────────────────────────────────────────────────────────

    def get_recent_events(self, limit: int = 50) -> list[dict]:
        """최근 이벤트 조회 — GET /v1/siem/events 엔드포인트용."""
        return [e.to_dict() for e in self._events[-limit:]]

    def get_events_from_log(self, limit: int = 100) -> list[dict]:
        """siem_events.jsonl 파일에서 이벤트 로드."""
        if not self.log_path.exists():
            return []
        lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        records = []
        for line in reversed(lines[-limit:]):
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records

    def daily_summary(self) -> dict:
        """오늘 하루 이벤트 통계."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        events = self.get_events_from_log(limit=1000)
        today_events = [e for e in events if e.get("timestamp", "").startswith(today)]
        by_severity: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for e in today_events:
            sev = e.get("severity", "unknown")
            cat = e.get("category", "unknown")
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_category[cat] = by_category.get(cat, 0) + 1
        return {
            "date": today,
            "total": len(today_events),
            "by_severity": by_severity,
            "by_category": by_category,
            "critical_actions": [
                e for e in today_events
                if e.get("action_recommended") == "block"
            ],
        }

    # ── 내부 ──────────────────────────────────────────────────────────

    def _record(self, event: SiemEvent) -> None:
        """이벤트를 인메모리 + JSONL 파일에 기록."""
        self._events.append(event)
        # 인메모리 최대 500건
        if len(self._events) > 500:
            self._events = self._events[-500:]
        # 파일 append
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")


# ── FastAPI 엔드포인트 헬퍼 ─────────────────────────────────────────

def create_siem_router():
    """
    FastAPI 라우터 생성 헬퍼.
    agent_gateway.py / fastapi_app.py에서 import하여 사용:

        from core.siem_engine import create_siem_router
        app.include_router(create_siem_router(), prefix="/v1/siem")
    """
    try:
        from fastapi import APIRouter
    except ImportError:
        return None

    router = APIRouter(tags=["AI-SIEM"])
    engine = SiemEngine()

    @router.get("/events")
    def get_siem_events(limit: int = 50):
        """최근 SIEM 이벤트 조회."""
        return {
            "events": engine.get_events_from_log(limit=limit),
            "total": limit,
        }

    @router.get("/cycle")
    def run_siem_cycle():
        """즉시 모니터링 사이클 실행 (테스트/수동 트리거용)."""
        return engine.run_cycle()

    @router.get("/summary")
    def get_siem_summary():
        """오늘 하루 이벤트 요약."""
        return engine.daily_summary()

    return router


# ── CLI 테스트 ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  AI-SIEM Engine — 단일 사이클 테스트")
    print("=" * 55)

    engine = SiemEngine()
    result = engine.run_cycle(agent_spirit_score=0.70)  # 낮은 Spirit 시뮬레이션

    print(f"수집 시각   : {result['cycle_at']}")
    print(f"데이터 소스 : {result['source_mode']}")
    print(f"이벤트 수   : {result['events_total']}")
    print(f"최고 심각도 : {result['highest_severity'].upper()}")
    print()

    for ev in result["events"]:
        sev_icon = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(ev["severity"], "·")
        print(f"{sev_icon} [{ev['severity'].upper()}] {ev['title']}")
        print(f"   → 권장 조치: {ev['action_recommended']}")
        print(f"   {ev['detail'][:80]}...")
        print()

    print(f"로그 저장: {SIEM_LOG_PATH}")
