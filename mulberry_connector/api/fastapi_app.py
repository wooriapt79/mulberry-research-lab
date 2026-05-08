# mulberry_connector/api/fastapi_app.py
"""
Mulberry Agent Execution API — 단일 진입점 (CSA Kbin 설계)


POST /v1/action/execute
  -> Spirit Score 검증 (류원)
  -> Hesitation 체크 (류원)
  -> Decision Code 결정 (Kbin)
  -> GitHub / SNS 게시


7개 에이전트 모두 이 하나의 API 사용.
agent 필드로 구분 — 개별 트리거 불필요.
"""


import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel


from core import PolicyEngine, Decision
from core.handoff import HandoffGate
from adapters.github import GitHubAdapter
from adapters.sns import SNSAdapter


app = FastAPI(
    title="Mulberry Connector API",
    description="Agent Execution Infrastructure — 'Systems where AI knows when NOT to act'",
    version="1.0.0",
)


GATEWAY_SECRET = os.environ.get("GATEWAY_SECRET", "mulberry-agent-relay-2026")
VALID_AGENTS   = {"koda", "kbin", "malu", "wayong", "ryuwon", "trang", "lynn", "jr"}


policy  = PolicyEngine()
handoff = HandoffGate()
github  = GitHubAdapter()
sns     = SNSAdapter()
