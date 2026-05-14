"""
Mulberry Agent Permission Approval System — #35

에이전트가 자신이 직접 소유하지 않은 도구를 사용하거나
capability_level L2 이상의 도구를 호출하려 할 때
submit → review → approve 워크플로우를 거치도록 강제한다.

설계 원칙 (장승배기 헌법):
  - "멈춤이 지혜다"   — L3/L4 는 항상 인간 검토 필수
  - "투명함은 신뢰다" — 모든 요청·결정은 3T 형식으로 아카이브
  - "기억은 공동체 것" — permission_log.jsonl 불변 보존

자동 승인 기준 (Spirit Gate 연동):
  L0 read-only    : spirit >= 0.75 → auto-approve
  L1 draft        : spirit >= 0.80 → auto-approve
  L2 external_post: spirit >= 0.80 → human review 필요
  L3 code_modify  : spirit >= 0.85 → human review 필요
  L4 deploy/fin   : 항상 human review + CRITICAL 에스컬레이션

설계: Koda (CTO) · RyuWon (윤리 검토) (2026-05-15)
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# ── 경로 ──────────────────────────────────────────────────────────
LOG_PATH = Path(__file__).parent.parent.parent / "jangseungbaegi_archive" / "permission_log.jsonl"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── 자동 승인 Spirit 기준 ─────────────────────────────────────────
AUTO_APPROVE_SPIRIT: dict[str, float] = {
    "L0": 0.75,
    "L1": 0.80,
    "L2": 999.0,   # 항상 human review
    "L3": 999.0,
    "L4": 999.0,
}

# 승인 유효 기간 (초)
APPROVAL_TTL: dict[str, float] = {
    "L0": 3600 * 8,    # 8시간
    "L1": 3600 * 4,    # 4시간
    "L2": 3600 * 2,    # 2시간
    "L3": 1800,        # 30분
    "L4": 900,         # 15분
}


class RequestStatus(str, Enum):
    PENDING     = "PENDING"        # 제출됨, 검토 대기
    IN_REVIEW   = "IN_REVIEW"      # 검토 중
    APPROVED    = "APPROVED"       # 승인됨
    AUTO_APPROVED = "AUTO_APPROVED"  # Spirit Gate 자동 승인
    REJECTED    = "REJECTED"       # 거절됨
    EXPIRED     = "EXPIRED"        # 유효 기간 만료
    CANCELLED   = "CANCELLED"      # 요청자 취소


@dataclass
class PermissionRequest:
    request_id:   str
    agent_id:     str           # 요청 에이전트
    tool_id:      str           # 요청 도구
    reason:       str           # 요청 이유
    spirit_score: float         # 요청 시점 Spirit Score
    capability_level: str       # L0~L4
    status:       RequestStatus = RequestStatus.PENDING
    requested_at: float = field(default_factory=time.time)
    reviewed_by:  str = ""      # 승인/거절한 에이전트 또는 "auto"
    reviewed_at:  float = 0.0
    review_note:  str = ""
    expires_at:   float = 0.0   # 승인 유효 기간 (APPROVED 시 설정)

    # ── 3T 투명성 보고서 ─────────────────────────────────────────
    def to_3t_report(self) -> dict:
        return {
            "3T_what": (
                f"[{self.status}] {self.agent_id} -> {self.tool_id} "
                f"(capability: {self.capability_level})"
            ),
            "3T_why": self.review_note or self.reason,
            "3T_how": (
                f"Spirit: {self.spirit_score:.2f} | "
                f"Reviewer: {self.reviewed_by or 'pending'} | "
                f"Expires: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(self.expires_at)) if self.expires_at else 'N/A'}"
            ),
        }

    def is_valid(self) -> bool:
        """현재 시점에서 유효한 승인인가?"""
        if self.status not in (RequestStatus.APPROVED, RequestStatus.AUTO_APPROVED):
            return False
        if self.expires_at and time.time() > self.expires_at:
            return False
        return True

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d


class ApprovalWorkflow:
    """
    권한 요청 워크플로우 관리자.

    흐름:
      submit() -> [auto-approve / IN_REVIEW] -> approve() or reject()
    """

    def __init__(self, registry=None):
        self._requests: dict[str, PermissionRequest] = {}
        self._registry = registry   # ToolRegistry (선택적 연동)

    # ── 제출 ────────────────────────────────────────────────────────
    def submit(
        self,
        agent_id: str,
        tool_id: str,
        reason: str,
        spirit_score: float,
        capability_level: str = "L1",
    ) -> PermissionRequest:
        """
        권한 요청 제출.
        Spirit Score 기준 충족 시 자동 승인, 미충족 시 human review 대기.
        """
        req = PermissionRequest(
            request_id=str(uuid.uuid4())[:12],
            agent_id=agent_id.lower(),
            tool_id=tool_id,
            reason=reason,
            spirit_score=spirit_score,
            capability_level=capability_level,
        )

        # 자동 승인 판단
        threshold = AUTO_APPROVE_SPIRIT.get(capability_level, 999.0)
        if spirit_score >= threshold:
            req.status = RequestStatus.AUTO_APPROVED
            req.reviewed_by = "spirit_gate_auto"
            req.reviewed_at = time.time()
            req.review_note = (
                f"Spirit Score {spirit_score:.2f} >= 임계값 {threshold:.2f} "
                f"(capability: {capability_level}) — 자동 승인"
            )
            req.expires_at = time.time() + APPROVAL_TTL.get(capability_level, 3600)
        else:
            req.status = RequestStatus.IN_REVIEW
            req.review_note = (
                f"Spirit Score {spirit_score:.2f} < 임계값 {threshold:.2f} "
                f"(capability: {capability_level}) — 인간 검토 필요"
            )

        self._requests[req.request_id] = req
        self._archive(req)
        return req

    # ── 승인 ────────────────────────────────────────────────────────
    def approve(
        self,
        request_id: str,
        reviewer: str,
        note: str = "",
    ) -> PermissionRequest:
        """인간 검토자(또는 시니어 에이전트)가 요청을 승인."""
        req = self._get_or_404(request_id)
        if req.status not in (RequestStatus.PENDING, RequestStatus.IN_REVIEW):
            raise ValueError(f"승인 불가 상태: {req.status}")

        req.status = RequestStatus.APPROVED
        req.reviewed_by = reviewer
        req.reviewed_at = time.time()
        req.review_note = note or "검토 후 승인"
        req.expires_at = time.time() + APPROVAL_TTL.get(req.capability_level, 3600)

        self._archive(req)
        return req

    # ── 거절 ────────────────────────────────────────────────────────
    def reject(
        self,
        request_id: str,
        reviewer: str,
        note: str = "",
    ) -> PermissionRequest:
        """요청 거절."""
        req = self._get_or_404(request_id)
        if req.status not in (RequestStatus.PENDING, RequestStatus.IN_REVIEW):
            raise ValueError(f"거절 불가 상태: {req.status}")

        req.status = RequestStatus.REJECTED
        req.reviewed_by = reviewer
        req.reviewed_at = time.time()
        req.review_note = note or "검토 후 거절"

        self._archive(req)
        return req

    # ── 취소 ────────────────────────────────────────────────────────
    def cancel(self, request_id: str, agent_id: str) -> PermissionRequest:
        """요청자 본인이 취소."""
        req = self._get_or_404(request_id)
        if req.agent_id != agent_id.lower():
            raise ValueError("요청자 본인만 취소할 수 있습니다.")
        if req.status not in (RequestStatus.PENDING, RequestStatus.IN_REVIEW):
            raise ValueError(f"취소 불가 상태: {req.status}")

        req.status = RequestStatus.CANCELLED
        req.reviewed_at = time.time()
        self._archive(req)
        return req

    # ── 권한 확인 ────────────────────────────────────────────────────
    def check_permission(self, agent_id: str, tool_id: str) -> bool:
        """현재 유효한 승인이 있는가?"""
        agent = agent_id.lower()
        # 만료 상태 갱신 먼저
        self._expire_stale()
        for req in self._requests.values():
            if req.agent_id == agent and req.tool_id == tool_id and req.is_valid():
                return True
        return False

    def get_active_approval(
        self, agent_id: str, tool_id: str
    ) -> Optional[PermissionRequest]:
        """유효한 승인 요청 반환 (없으면 None)."""
        agent = agent_id.lower()
        self._expire_stale()
        for req in self._requests.values():
            if req.agent_id == agent and req.tool_id == tool_id and req.is_valid():
                return req
        return None

    # ── 조회 ─────────────────────────────────────────────────────────
    def get(self, request_id: str) -> Optional[PermissionRequest]:
        return self._requests.get(request_id)

    def pending_requests(self) -> list[PermissionRequest]:
        """검토 대기 중인 요청 목록."""
        self._expire_stale()
        return [
            r for r in self._requests.values()
            if r.status in (RequestStatus.PENDING, RequestStatus.IN_REVIEW)
        ]

    def requests_by_agent(self, agent_id: str) -> list[PermissionRequest]:
        """특정 에이전트의 모든 요청."""
        return [
            r for r in self._requests.values()
            if r.agent_id == agent_id.lower()
        ]

    def summary(self) -> dict:
        self._expire_stale()
        counts: dict[str, int] = {}
        for r in self._requests.values():
            counts[r.status.value] = counts.get(r.status.value, 0) + 1
        return {
            "total": len(self._requests),
            "by_status": counts,
            "pending_count": len(self.pending_requests()),
        }

    # ── 내부 유틸 ────────────────────────────────────────────────────
    def _get_or_404(self, request_id: str) -> PermissionRequest:
        req = self._requests.get(request_id)
        if not req:
            raise KeyError(f"요청을 찾을 수 없습니다: {request_id}")
        return req

    def _expire_stale(self):
        """만료된 승인을 EXPIRED 상태로 갱신."""
        now = time.time()
        for req in self._requests.values():
            if (
                req.status in (RequestStatus.APPROVED, RequestStatus.AUTO_APPROVED)
                and req.expires_at
                and now > req.expires_at
            ):
                req.status = RequestStatus.EXPIRED

    def _archive(self, req: PermissionRequest):
        """장승배기 아카이브 — append-only 기록."""
        entry = req.to_dict()
        entry["_3t"] = req.to_3t_report()
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass   # 파일 I/O 실패 시 무시 (메모리 상태는 유지)


# ── Singleton ────────────────────────────────────────────────────
_workflow = ApprovalWorkflow()


# ── FastAPI Pydantic 모델 ─────────────────────────────────────────

class SubmitRequest(BaseModel):
    agent_id: str
    tool_id: str
    reason: str
    spirit_score: float = 0.80
    capability_level: str = "L1"


class ReviewAction(BaseModel):
    reviewer: str
    note: str = ""


# ── FastAPI 라우터 ────────────────────────────────────────────────

def create_approval_router() -> APIRouter:
    """
    /v1/permissions/* 라우터 팩토리.

    엔드포인트:
      POST   /v1/permissions/request              — 권한 요청 제출
      GET    /v1/permissions/pending              — 대기 요청 목록 (Steward Console)
      GET    /v1/permissions/summary              — 현황 요약
      GET    /v1/permissions/{id}                 — 요청 상태 조회
      POST   /v1/permissions/{id}/approve         — 승인
      POST   /v1/permissions/{id}/reject          — 거절
      DELETE /v1/permissions/{id}                 — 취소
      GET    /v1/permissions/check/{agent}/{tool} — 유효 승인 여부 확인
    """
    router = APIRouter()

    @router.post("/request", summary="권한 요청 제출")
    def submit_request(body: SubmitRequest):
        req = _workflow.submit(
            agent_id=body.agent_id,
            tool_id=body.tool_id,
            reason=body.reason,
            spirit_score=body.spirit_score,
            capability_level=body.capability_level,
        )
        return {
            "request_id": req.request_id,
            "status": req.status.value,
            "auto_approved": req.status == RequestStatus.AUTO_APPROVED,
            "review_note": req.review_note,
            "expires_at": req.expires_at or None,
            "3t": req.to_3t_report(),
        }

    @router.get("/pending", summary="대기 중인 요청 목록 (Steward Console 용)")
    def list_pending():
        pending = _workflow.pending_requests()
        return {
            "count": len(pending),
            "requests": [r.to_dict() for r in pending],
        }

    @router.get("/summary", summary="권한 요청 현황 요약")
    def get_summary():
        return _workflow.summary()

    @router.get("/check/{agent_id}/{tool_id}", summary="유효 승인 여부 확인")
    def check_permission(agent_id: str, tool_id: str):
        req = _workflow.get_active_approval(agent_id, tool_id)
        return {
            "agent_id": agent_id,
            "tool_id": tool_id,
            "has_permission": req is not None,
            "request_id": req.request_id if req else None,
            "expires_at": req.expires_at if req else None,
            "status": req.status.value if req else None,
        }

    @router.get("/{request_id}", summary="요청 상태 조회")
    def get_request(request_id: str):
        req = _workflow.get(request_id)
        if not req:
            raise HTTPException(status_code=404, detail=f"요청 없음: {request_id}")
        return req.to_dict()

    @router.post("/{request_id}/approve", summary="요청 승인")
    def approve_request(request_id: str, body: ReviewAction):
        try:
            req = _workflow.approve(request_id, body.reviewer, body.note)
        except (KeyError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {
            "request_id": req.request_id,
            "status": req.status.value,
            "approved_by": req.reviewed_by,
            "expires_at": req.expires_at,
            "3t": req.to_3t_report(),
        }

    @router.post("/{request_id}/reject", summary="요청 거절")
    def reject_request(request_id: str, body: ReviewAction):
        try:
            req = _workflow.reject(request_id, body.reviewer, body.note)
        except (KeyError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {
            "request_id": req.request_id,
            "status": req.status.value,
            "rejected_by": req.reviewed_by,
            "note": req.review_note,
        }

    @router.delete("/{request_id}", summary="요청 취소")
    def cancel_request(request_id: str, agent_id: str):
        try:
            req = _workflow.cancel(request_id, agent_id)
        except (KeyError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"request_id": req.request_id, "status": req.status.value}

    return router


# ── 외부 접근용 ───────────────────────────────────────────────────
def get_workflow() -> ApprovalWorkflow:
    """전역 워크플로우 인스턴스 반환 (다른 모듈에서 check_permission 호출용)."""
    return _workflow
