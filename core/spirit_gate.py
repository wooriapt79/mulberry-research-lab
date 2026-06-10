# -*- coding: utf-8 -*-
"""
Spirit Gate API endpoint - exposes scripts/spirit_gate.py's SpiritGate engine
over HTTP for STEP 4 (Kbin auto-review).

Endpoint:
    POST /v1/spirit-gate
    body: {"code": "<source text>", "score_threshold": 0.85}
    returns: SpiritGate.run() result, with "passed" reflecting score_threshold
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from scripts.spirit_gate import SpiritGate, SPIRIT_THRESHOLD

router = APIRouter()


class SpiritGateRequest(BaseModel):
    code: str = Field(..., description="Source code or text to evaluate")
    score_threshold: float = Field(SPIRIT_THRESHOLD, ge=0.0, le=1.0)


class SpiritGateResponse(BaseModel):
    stage: str
    status: str
    spirit_score: float
    threshold: float
    passed: bool
    violations_critical: list[str]
    violations_warning: list[str]
    spirit_bonus: list[str]
    human_review_required: bool


@router.post("/v1/spirit-gate", response_model=SpiritGateResponse)
def evaluate_spirit_gate(request: SpiritGateRequest) -> SpiritGateResponse:
    gate = SpiritGate(threshold=request.score_threshold)
    result = gate.run(request.code, source="api:/v1/spirit-gate")

    return SpiritGateResponse(
        stage=result["stage"],
        status=result["status"],
        spirit_score=result["spirit_score"],
        threshold=result["threshold"],
        passed=result["spirit_score"] >= request.score_threshold,
        violations_critical=result["violations_critical"],
        violations_warning=result["violations_warning"],
        spirit_bonus=result["spirit_bonus"],
        human_review_required=result["human_review_required"],
    )
