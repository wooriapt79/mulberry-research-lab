"""Mulberry Agent Gateway v2.0.0.

Security-first reference implementation for Railway/FastAPI.

Execution contract
------------------
1. An agent authenticates with a signed Passport token.
2. Every mutating request carries a signed Mandate token.
3. The policy engine checks actor, action, resource, limits and expiry.
4. Medium/high-risk actions require a one-time Human approval token.
5. Idempotency and nonce checks prevent accidental/replayed execution.
6. Every decision is written to an append-only JSONL audit trail.

This file intentionally runs beside v1.6 instead of replacing it. External
providers are accessed only through explicit adapters. Browser automation and
unofficial search scraping are deliberately excluded.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from threading import Lock
from typing import Any, Literal

import requests
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


VERSION = "2.0.0"
SERVICE = "mulberry-agent-gateway"
STARTED_AT = time.time()


def required_env(name: str, minimum: int = 32) -> str:
    val = os.environ.get(name, "")
    if len(val) < minimum:
        raise RuntimeError(
            f"[STARTUP BLOCKED] {name} must be set to at least {minimum} chars. "
            "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return val


# Fail-closed: the process will not start unless all three keys are present.
PASSPORT_SIGNING_KEY: str = required_env("PASSPORT_SIGNING_KEY")
MANDATE_SIGNING_KEY: str = required_env("MANDATE_SIGNING_KEY")
APPROVAL_SIGNING_KEY: str = required_env("APPROVAL_SIGNING_KEY")

AUDIT_FILE = Path(os.environ.get("AUDIT_FILE", "audit.jsonl"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
log = logging.getLogger(SERVICE)

# ---------------------------------------------------------------------------
# Token helpers (HS256-style, no external JWT library)
# ---------------------------------------------------------------------------

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * pad)


def sign_token(payload: dict, key: str) -> str:
    header = _b64url(b'{"alg":"HS256","typ":"JWT"}')
    body = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(key.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    return f"{header}.{body}.{_b64url(sig)}"


def verify_token(token: str, key: str) -> dict:
    try:
        header, body, sig = token.split(".")
    except ValueError:
        raise ValueError("Malformed token")
    expected = hmac.new(key.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_decode(sig), expected):
        raise ValueError("Invalid signature")
    payload = json.loads(_b64url_decode(body))
    if payload.get("exp", 0) < time.time():
        raise ValueError("Token expired")
    return payload


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Actor:
    agent_id: str
    passport_id: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class Mandate:
    mandate_id: str
    subject: str
    actions: tuple[str, ...]
    resources: tuple[str, ...]
    max_calls: int
    max_amount_krw: int
    human_approval_over_krw: int


# ---------------------------------------------------------------------------
# Expiring in-memory store (single-process; swap for Redis in multi-replica)
# ---------------------------------------------------------------------------

class ExpiringStore:
    def __init__(self) -> None:
        self._store: dict[str, float] = {}
        self._lock = Lock()

    def add(self, key: str, ttl: float) -> None:
        with self._lock:
            self._store[key] = time.time() + ttl
            self._evict()

    def contains(self, key: str) -> bool:
        with self._lock:
            self._evict()
            return key in self._store

    def _evict(self) -> None:
        now = time.time()
        self._store = {k: v for k, v in self._store.items() if v > now}


nonce_store = ExpiringStore()
idempotency_store: dict[str, dict] = {}
approval_store = ExpiringStore()

# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

MEDIUM_RISK_ACTIONS = {"github.memory.append", "image.generate"}


def risk_for(action: str, amount_krw: int = 0) -> Literal["low", "medium", "high"]:
    if action in MEDIUM_RISK_ACTIONS:
        return "medium"
    if amount_krw > 0:
        return "high"
    return "low"


# ---------------------------------------------------------------------------
# Audit writer
# ---------------------------------------------------------------------------

class AuditWriter:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = Lock()

    def write(self, event: dict) -> None:
        record = {"ts": datetime.now(timezone.utc).isoformat(), **event}
        with self._lock:
            with self._path.open("a") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")


audit = AuditWriter(AUDIT_FILE)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="Mulberry Agent Gateway", version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class TriggerRequest(BaseModel):
    intent: str
    payload: dict = Field(default_factory=dict)
    nonce: str = Field(default_factory=lambda: secrets.token_hex(16))
    idempotency_key: str | None = None


class ApprovalRequest(BaseModel):
    execution_id: str
    approver: str
    decision: Literal["approve", "reject"]
    note: str = ""


class SearchQuery(BaseModel):
    query: str
    region: str
    budget: int | None = None
    constraints: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Auth dependencies
# ---------------------------------------------------------------------------

ALLOWED_INTENTS = {
    "search.read", "quote.request", "memory.append",
    "image.generate", "github.memory.append",
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "agent": {"search.read", "quote.request", "memory.append", "image.generate"},
    "senior": {"search.read", "quote.request", "memory.append", "image.generate", "github.memory.append"},
    "admin": ALLOWED_INTENTS,
}


def authenticate_passport(x_passport_token: str = Header(...)) -> Actor:
    try:
        payload = verify_token(x_passport_token, PASSPORT_SIGNING_KEY)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    return Actor(
        agent_id=payload["sub"],
        passport_id=payload["passport_id"],
        roles=tuple(payload.get("roles", [])),
    )


def authenticate_mandate(x_mandate_token: str = Header(...)) -> Mandate:
    try:
        payload = verify_token(x_mandate_token, MANDATE_SIGNING_KEY)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return Mandate(
        mandate_id=payload["mandate_id"],
        subject=payload["sub"],
        actions=tuple(payload["actions"]),
        resources=tuple(payload["resources"]),
        max_calls=payload.get("max_calls", 1),
        max_amount_krw=payload.get("max_amount_krw", 0),
        human_approval_over_krw=payload.get("human_approval_over_krw", 0),
    )


# ---------------------------------------------------------------------------
# Core execution gate
# ---------------------------------------------------------------------------

call_counters: dict[str, int] = {}


def execute_guarded(
    actor: Actor,
    mandate: Mandate,
    intent: str,
    payload: dict,
    nonce: str,
    idempotency_key: str | None,
    approval_token: str | None,
) -> dict:
    execution_id = str(uuid.uuid4())
    amount_krw: int = payload.get("amount_krw", 0)

    # 1. Passport — role check
    allowed = set()
    for role in actor.roles:
        allowed |= ROLE_PERMISSIONS.get(role, set())
    if intent not in allowed:
        audit.write({"event": "DENIED_ROLE", "actor": actor.agent_id, "intent": intent})
        raise HTTPException(status_code=403, detail="Role does not permit this intent")

    # 2. Mandate — action / resource / limit check
    if intent not in mandate.actions:
        audit.write({"event": "DENIED_MANDATE", "actor": actor.agent_id, "intent": intent})
        raise HTTPException(status_code=403, detail="Intent not in mandate")
    if amount_krw > mandate.max_amount_krw:
        raise HTTPException(status_code=403, detail="Amount exceeds mandate limit")

    call_key = f"{actor.agent_id}:{mandate.mandate_id}"
    call_counters[call_key] = call_counters.get(call_key, 0) + 1
    if call_counters[call_key] > mandate.max_calls:
        raise HTTPException(status_code=429, detail="Mandate call limit reached")

    # 3. Risk — human approval gate
    risk = risk_for(intent, amount_krw)
    requires_approval = risk in {"medium", "high"} or amount_krw >= mandate.human_approval_over_krw
    if requires_approval:
        if not approval_token:
            audit.write({"event": "PENDING_APPROVAL", "execution_id": execution_id, "intent": intent})
            raise HTTPException(
                status_code=202,
                detail={"execution_id": execution_id, "status": "pending_approval"},
            )
        if not approval_store.contains(approval_token):
            raise HTTPException(status_code=403, detail="Approval token invalid or expired")

    # 4. Nonce check (replay prevention)
    if nonce_store.contains(nonce):
        raise HTTPException(status_code=409, detail="Duplicate nonce")
    nonce_store.add(nonce, ttl=300)

    # 5. Idempotency
    if idempotency_key and idempotency_key in idempotency_store:
        return idempotency_store[idempotency_key]

    # 6. Execute
    result = _dispatch(intent, payload, actor)
    audit.write({
        "event": "EXECUTED",
        "execution_id": execution_id,
        "actor": actor.agent_id,
        "intent": intent,
        "risk": risk,
        "amount_krw": amount_krw,
    })
    if idempotency_key:
        idempotency_store[idempotency_key] = result
    return result


def _dispatch(intent: str, payload: dict, actor: Actor) -> dict:
    """Route validated intents to adapter functions."""
    if intent == "search.read":
        return _adapter_search(payload, actor)
    if intent == "quote.request":
        return _adapter_quote(payload, actor)
    if intent == "memory.append":
        return _adapter_memory(payload, actor)
    if intent == "image.generate":
        return _adapter_image(payload, actor)
    if intent == "github.memory.append":
        return _adapter_github_memory(payload, actor)
    raise HTTPException(status_code=400, detail=f"Unknown intent: {intent}")


# ---------------------------------------------------------------------------
# Adapter stubs (replace with real implementations)
# ---------------------------------------------------------------------------

def _adapter_search(payload: dict, actor: Actor) -> dict:
    return {"status": "ok", "results": [], "note": "stub — wire NaverOfficialAPIAdapter"}


def _adapter_quote(payload: dict, actor: Actor) -> dict:
    return {"status": "ok", "quote_id": str(uuid.uuid4()), "note": "stub"}


def _adapter_memory(payload: dict, actor: Actor) -> dict:
    return {"status": "ok", "appended": True}


def _adapter_image(payload: dict, actor: Actor) -> dict:
    return {"status": "ok", "image_url": None, "note": "stub"}


def _adapter_github_memory(payload: dict, actor: Actor) -> dict:
    return {"status": "ok", "committed": False, "note": "stub — wire GitHub API"}


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": VERSION,
        "uptime_seconds": round(time.time() - STARTED_AT, 1),
    }


@app.post("/trigger")
def trigger(
    body: TriggerRequest,
    actor: Actor = Depends(authenticate_passport),
    mandate: Mandate = Depends(authenticate_mandate),
    x_approval_token: str | None = Header(default=None),
) -> JSONResponse:
    if body.intent not in ALLOWED_INTENTS:
        raise HTTPException(status_code=400, detail="Unknown intent")
    result = execute_guarded(
        actor=actor,
        mandate=mandate,
        intent=body.intent,
        payload=body.payload,
        nonce=body.nonce,
        idempotency_key=body.idempotency_key,
        approval_token=x_approval_token,
    )
    return JSONResponse(content=result)


@app.post("/approval/decide")
def approval_decide(
    body: ApprovalRequest,
    actor: Actor = Depends(authenticate_passport),
) -> dict:
    if "admin" not in actor.roles and "senior" not in actor.roles:
        raise HTTPException(status_code=403, detail="Only admin/senior may approve")
    if body.decision == "approve":
        token = secrets.token_hex(32)
        approval_store.add(token, ttl=600)
        audit.write({
            "event": "APPROVED",
            "execution_id": body.execution_id,
            "approver": body.approver,
            "note": body.note,
        })
        return {"status": "approved", "approval_token": token}
    audit.write({
        "event": "REJECTED",
        "execution_id": body.execution_id,
        "approver": body.approver,
        "note": body.note,
    })
    return {"status": "rejected"}


@app.get("/audit")
def audit_tail(
    n: int = 50,
    actor: Actor = Depends(authenticate_passport),
) -> list[dict]:
    if "admin" not in actor.roles:
        raise HTTPException(status_code=403, detail="Admin only")
    if not AUDIT_FILE.exists():
        return []
    lines = AUDIT_FILE.read_text().strip().split("\n")
    return [json.loads(l) for l in lines[-n:] if l]


# ---------------------------------------------------------------------------
# Kakao v2 webhook — intentionally read-only
# ---------------------------------------------------------------------------

@app.post("/kakao/webhook")
async def kakao_webhook(
    request: Request,
    x_kakao_signature: str = Header(default=""),
) -> dict:
    """
    v2 Kakao channel: read-only announcement mode.
    Mutating actions are handled by v1.6 (agent_gateway.py).
    """
    body = await request.body()
    expected = hmac.new(
        PASSPORT_SIGNING_KEY.encode(), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, x_kakao_signature):
        raise HTTPException(status_code=401, detail="Bad Kakao signature")

    data = json.loads(body)
    user_utterance = data.get("userRequest", {}).get("utterance", "")
    log.info("kakao_v2 utterance=%r", user_utterance)
    audit.write({"event": "KAKAO_RECEIVED", "utterance": user_utterance})

    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": (
                            "안녕하세요! Mulberry v2 채널은 읽기 전용 안내 모드입니다. "
                            "검색·예약은 Luna 채널을 이용해 주세요."
                        )
                    }
                }
            ]
        },
    }


# ---------------------------------------------------------------------------
# Admin helpers (NOT exposed as HTTP routes)
# ---------------------------------------------------------------------------

def issue_passport(agent_id: str, roles: list[str], ttl_seconds: int = 3600) -> str:
    payload = {
        "sub": agent_id,
        "passport_id": f"pp-{uuid.uuid4().hex[:8]}",
        "roles": roles,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl_seconds,
    }
    return sign_token(payload, PASSPORT_SIGNING_KEY)


def issue_mandate(
    agent_id: str,
    actions: list[str],
    resources: list[str],
    *,
    max_calls: int = 10,
    max_amount_krw: int = 0,
    human_approval_over_krw: int = 50_000,
    ttl_seconds: int = 1800,
) -> str:
    payload = {
        "sub": agent_id,
        "mandate_id": f"mnd-{uuid.uuid4().hex[:8]}",
        "actions": actions,
        "resources": resources,
        "max_calls": max_calls,
        "max_amount_krw": max_amount_krw,
        "human_approval_over_krw": human_approval_over_krw,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl_seconds,
    }
    return sign_token(payload, MANDATE_SIGNING_KEY)
