"""
Railway Monitor Adapter — AI-SIEM 데이터 소스

역할:
  Railway 인프라에서 HTTP 트래픽, 메트릭, 에러율 데이터를 수집하여
  AI-SIEM 엔진(siem_engine.py)으로 전달하는 어댑터.

공유 레이어 연결:
  tool_registry.yaml → railway.logs (L0, primary_data_source)
  tool_registry.yaml → railway.metrics (L0, primary_data_source)

데이터 흐름:
  Railway GraphQL API → MetricSnapshot → SiemEngine.analyze()

환경변수:
  RAILWAY_API_TOKEN  : Railway API 토큰 (필수 — 없으면 Mock 모드)
  RAILWAY_PROJECT_ID : 대상 프로젝트 ID (선택)
  RAILWAY_ENV_ID     : 대상 환경 ID (선택)

설계: re.eul + Koda (2026-05-12)
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


# ── 설정 ────────────────────────────────────────────────────────────
RAILWAY_GQL_URL = "https://backboard.railway.app/graphql/v2"
RAILWAY_API_TOKEN = os.environ.get("RAILWAY_API_TOKEN", "")
RAILWAY_PROJECT_ID = os.environ.get("RAILWAY_PROJECT_ID", "")
RAILWAY_ENV_ID = os.environ.get("RAILWAY_ENV_ID", "")

# 수집 주기 기본값 (초)
DEFAULT_POLL_INTERVAL_SEC = 60


# ── 데이터 모델 ─────────────────────────────────────────────────────

@dataclass
class HttpTrafficSample:
    """단일 HTTP 로그 이벤트."""
    timestamp: str
    method: str
    path: str
    status_code: int
    response_ms: float
    src_ip: str = ""
    edge_region: str = ""


@dataclass
class MetricSnapshot:
    """
    Railway 서비스 전체 메트릭 스냅샷.
    siem_engine.py가 이 구조를 기반으로 이상 탐지를 수행한다.
    """
    collected_at: str                          # ISO 8601 UTC
    service_id: str
    environment_id: str
    is_mock: bool = False                      # True = RAILWAY_API_TOKEN 없음

    # HTTP 트래픽
    req_count_total: int = 0
    req_count_2xx: int = 0
    req_count_4xx: int = 0
    req_count_5xx: int = 0
    error_rate_5xx: float = 0.0               # 0.0~1.0
    error_rate_4xx: float = 0.0

    # 응답 시간 (ms)
    latency_p50_ms: float = 0.0
    latency_p90_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0

    # 네트워크
    network_tx_gb: float = 0.0
    network_rx_gb: float = 0.0

    # 인프라
    cpu_percent: float = 0.0
    memory_mb: float = 0.0

    # 최근 HTTP 이벤트 (이상 IP 탐지 등)
    recent_http: list[HttpTrafficSample] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["recent_http"] = [asdict(h) for h in self.recent_http]
        return d


# ── Railway GraphQL 클라이언트 ───────────────────────────────────────

class RailwayClient:
    """Railway GraphQL API v2 최소 클라이언트."""

    def __init__(self, token: str = RAILWAY_API_TOKEN):
        self.token = token

    def _query(self, gql: str, variables: dict | None = None) -> dict:
        payload = json.dumps(
            {"query": gql, "variables": variables or {}}
        ).encode("utf-8")
        req = urllib.request.Request(
            RAILWAY_GQL_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_services(self, project_id: str) -> list[dict]:
        """프로젝트 내 서비스 목록 조회."""
        gql = """
        query Services($projectId: String!) {
          project(id: $projectId) {
            services { edges { node { id name } } }
          }
        }
        """
        try:
            data = self._query(gql, {"projectId": project_id})
            edges = (
                data.get("data", {})
                    .get("project", {})
                    .get("services", {})
                    .get("edges", [])
            )
            return [e["node"] for e in edges]
        except Exception:
            return []

    def get_deployments(self, environment_id: str) -> list[dict]:
        """최근 배포 이력 조회."""
        gql = """
        query Deployments($environmentId: String!) {
          deployments(
            input: { environmentId: $environmentId }
            first: 5
          ) {
            edges { node {
              id status createdAt
              service { name }
            }}
          }
        }
        """
        try:
            data = self._query(gql, {"environmentId": environment_id})
            edges = (
                data.get("data", {})
                    .get("deployments", {})
                    .get("edges", [])
            )
            return [e["node"] for e in edges]
        except Exception:
            return []


# ── 메트릭 파서 ─────────────────────────────────────────────────────

def _parse_log_line(line: str) -> Optional[HttpTrafficSample]:
    """
    Railway 로그 라인에서 HTTP 이벤트 파싱.
    예: '2026-05-12T09:00:00Z GET /api/v1/tools 200 45ms 1.2.3.4'
    """
    parts = line.strip().split()
    if len(parts) < 5:
        return None
    try:
        ts = parts[0] if "T" in parts[0] else datetime.now(timezone.utc).isoformat()
        method = parts[1] if parts[1] in ("GET", "POST", "PUT", "DELETE", "PATCH") else "GET"
        path = parts[2] if parts[2].startswith("/") else "/unknown"
        status = int(parts[3]) if parts[3].isdigit() else 0
        ms_str = parts[4].replace("ms", "")
        ms = float(ms_str) if ms_str.replace(".", "").isdigit() else 0.0
        src_ip = parts[5] if len(parts) > 5 else ""
        return HttpTrafficSample(
            timestamp=ts, method=method, path=path,
            status_code=status, response_ms=ms, src_ip=src_ip
        )
    except (ValueError, IndexError):
        return None


def _compute_rates(samples: list[HttpTrafficSample]) -> dict:
    """HTTP 샘플에서 에러율·응답시간 백분위 계산."""
    if not samples:
        return {
            "req_count_total": 0, "req_count_2xx": 0,
            "req_count_4xx": 0, "req_count_5xx": 0,
            "error_rate_5xx": 0.0, "error_rate_4xx": 0.0,
            "latency_p50_ms": 0.0, "latency_p90_ms": 0.0,
            "latency_p95_ms": 0.0, "latency_p99_ms": 0.0,
        }

    total = len(samples)
    count_2xx = sum(1 for s in samples if 200 <= s.status_code < 300)
    count_4xx = sum(1 for s in samples if 400 <= s.status_code < 500)
    count_5xx = sum(1 for s in samples if 500 <= s.status_code < 600)

    latencies = sorted(s.response_ms for s in samples)

    def percentile(lst: list[float], pct: float) -> float:
        if not lst:
            return 0.0
        idx = max(0, int(len(lst) * pct / 100) - 1)
        return lst[idx]

    return {
        "req_count_total": total,
        "req_count_2xx": count_2xx,
        "req_count_4xx": count_4xx,
        "req_count_5xx": count_5xx,
        "error_rate_5xx": round(count_5xx / total, 4) if total else 0.0,
        "error_rate_4xx": round(count_4xx / total, 4) if total else 0.0,
        "latency_p50_ms": percentile(latencies, 50),
        "latency_p90_ms": percentile(latencies, 90),
        "latency_p95_ms": percentile(latencies, 95),
        "latency_p99_ms": percentile(latencies, 99),
    }


# ── Mock 데이터 ──────────────────────────────────────────────────────

def _mock_snapshot() -> MetricSnapshot:
    """
    RAILWAY_API_TOKEN 없을 때 반환하는 Mock 스냅샷.
    연결 테스트 전 개발·테스트 환경에서 사용.
    실제 연결 시 이 함수는 호출되지 않음.
    """
    import random
    rng = random.Random(int(time.time()) // 60)  # 분 단위로 값 변동

    # 정상 범위 Mock — 가끔 경보 시뮬레이션
    spike = rng.random() < 0.1  # 10% 확률로 에러율 급등 시뮬레이션

    samples = []
    for i in range(rng.randint(80, 120)):
        status = 500 if (spike and i < 20) else rng.choices(
            [200, 201, 400, 404, 500],
            weights=[70, 10, 8, 7, 5]
        )[0]
        samples.append(HttpTrafficSample(
            timestamp=datetime.now(timezone.utc).isoformat(),
            method=rng.choice(["GET", "POST", "GET", "GET"]),
            path=rng.choice(["/v1/tools", "/v1/action/execute", "/health", "/v1/tools/call"]),
            status_code=status,
            response_ms=rng.uniform(30, 3000 if spike else 300),
            src_ip=f"1.2.3.{rng.randint(1, 255)}",
            edge_region=rng.choice(["asia-northeast1", "us-west1"]),
        ))

    rates = _compute_rates(samples)
    return MetricSnapshot(
        collected_at=datetime.now(timezone.utc).isoformat(),
        service_id="mock-service",
        environment_id="mock-env",
        is_mock=True,
        **rates,
        network_tx_gb=round(rng.uniform(0.1, 2.0), 3),
        network_rx_gb=round(rng.uniform(0.05, 1.0), 3),
        cpu_percent=round(rng.uniform(5, 60 if spike else 30), 1),
        memory_mb=round(rng.uniform(128, 512), 1),
        recent_http=samples[-20:],  # 최근 20건만
    )


# ── 메인 모니터 클래스 ───────────────────────────────────────────────

class RailwayMonitor:
    """
    Railway 인프라 메트릭 수집기.

    사용법:
        monitor = RailwayMonitor()
        snapshot = monitor.snapshot()
        print(snapshot.error_rate_5xx)

    RAILWAY_API_TOKEN이 없으면 자동으로 Mock 모드로 동작.
    공식 연결 완료 후 동일한 인터페이스로 실제 데이터 반환.
    """

    def __init__(
        self,
        api_token: str = RAILWAY_API_TOKEN,
        project_id: str = RAILWAY_PROJECT_ID,
        environment_id: str = RAILWAY_ENV_ID,
    ):
        self.api_token = api_token
        self.project_id = project_id
        self.environment_id = environment_id
        self._client = RailwayClient(api_token) if api_token else None
        self._baseline: Optional[MetricSnapshot] = None  # 이상 탐지 기준선

    @property
    def is_connected(self) -> bool:
        """Railway API 연결 여부."""
        return bool(self.api_token)

    def snapshot(self) -> MetricSnapshot:
        """
        현재 메트릭 스냅샷 반환.
        API 연결 없으면 Mock 반환.
        """
        if not self.is_connected:
            snap = _mock_snapshot()
            return snap

        try:
            return self._fetch_live_snapshot()
        except Exception as exc:
            # API 오류 시 Mock으로 graceful 대체
            snap = _mock_snapshot()
            snap.is_mock = True
            return snap

    def _fetch_live_snapshot(self) -> MetricSnapshot:
        """
        Railway API에서 실제 메트릭 수집.
        Railway 공식 연결 완료 후 이 메서드가 실 데이터를 반환함.
        현재: deployments 상태 조회 → 향후 metrics 쿼리 확장 예정.
        """
        assert self._client is not None

        # 배포 상태 조회 (현재 구현된 Railway GraphQL 기능)
        deployments = []
        if self.environment_id:
            deployments = self._client.get_deployments(self.environment_id)

        # 배포 상태 기반 기초 헬스 평가
        latest_status = deployments[0].get("status", "UNKNOWN") if deployments else "UNKNOWN"
        # SUCCESS → 정상, FAILED/CRASHED → 에러 시그널
        base_error = 0.0 if latest_status in ("SUCCESS", "DEPLOYING") else 0.12

        # 메트릭 쿼리 (Railway GraphQL 메트릭 API 확장 예정)
        # TODO: Railway 공식 발표 후 metrics 쿼리 활성화
        # measurements = ["HTTP_REQUEST_COUNT", "NETWORK_TX_GB", "CPU_USAGE", ...]

        return MetricSnapshot(
            collected_at=datetime.now(timezone.utc).isoformat(),
            service_id=self.project_id or "connected",
            environment_id=self.environment_id or "connected",
            is_mock=False,
            req_count_total=0,      # 향후 Railway metrics API 연동
            error_rate_5xx=base_error,
            error_rate_4xx=0.0,
            latency_p50_ms=0.0,
            latency_p90_ms=0.0,
            latency_p95_ms=0.0,
            latency_p99_ms=0.0,
            network_tx_gb=0.0,
            network_rx_gb=0.0,
            cpu_percent=0.0,
            memory_mb=0.0,
            recent_http=[],
        )

    def update_baseline(self, snapshot: MetricSnapshot) -> None:
        """현재 스냅샷을 이상 탐지 기준선으로 저장."""
        self._baseline = snapshot

    def get_baseline(self) -> Optional[MetricSnapshot]:
        """저장된 기준선 반환."""
        return self._baseline

    def service_summary(self) -> dict:
        """간단한 서비스 현황 요약."""
        connected = self.is_connected
        return {
            "connected": connected,
            "mode": "live" if connected else "mock",
            "project_id": self.project_id or "not_set",
            "environment_id": self.environment_id or "not_set",
            "api_token_set": bool(self.api_token),
        }


# ── CLI 테스트 ────────────────────────────────────────────────────────

if __name__ == "__main__":
    monitor = RailwayMonitor()
    print(f"모드: {'Live' if monitor.is_connected else 'Mock (RAILWAY_API_TOKEN 없음)'}")
    snap = monitor.snapshot()
    print(f"수집 시각  : {snap.collected_at}")
    print(f"총 요청 수 : {snap.req_count_total}")
    print(f"5xx 에러율 : {snap.error_rate_5xx:.2%}")
    print(f"4xx 에러율 : {snap.error_rate_4xx:.2%}")
    print(f"p99 응답   : {snap.latency_p99_ms:.0f}ms")
    print(f"CPU        : {snap.cpu_percent:.1f}%")
    print(f"Mock 여부  : {snap.is_mock}")
