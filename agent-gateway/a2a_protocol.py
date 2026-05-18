"""
a2a_protocol.py — Mulberry Agent-to-Agent 프로토콜 v1.0
=======================================================
Spec: trang-chat-socketio-a2a-spec-20260518.md

에이전트가 다른 에이전트에게 직접 작업을 위임하는 비동기 메시지 프로토콜.

FastAPI Router로 구현 → agent_gateway.py 에 마운트:
  from a2a_protocol import a2a_router, get_inbox, broadcast_to_all
  app.include_router(a2a_router, prefix="/a2a")

엔드포인트:
  POST /a2a/send              에이전트 간 메시지 전송
  GET  /a2a/inbox/{agent_id}  에이전트 수신함 조회
  GET  /a2a/thread/{thread_id} 스레드 전체 조회
  POST /a2a/broadcast         전체 에이전트 브로드캐스트
  GET  /a2a/status            A2A 시스템 상태

MVP: 인메모리 큐 (Phase 2에서 Redis/DB로 마이그레이션 예정)
"""

from __future__ import annotations

import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# ── 상수 ────────────────────────────────────────────────────────
A2A_VERSION = "1.0"
INBOX_MAX_SIZE = 100       # 에이전트당 최대 수신함 크기
THREAD_MAX_SIZE = 200      # 스레드당 최대 메시지 수

# ── 인메모리 저장소 ──────────────────────────────────────────────
# inbox[agent_id] = deque of messages
_inbox: dict[str, deque] = defaultdict(lambda: deque(maxlen=INBOX_MAX_SIZE))
# threads[thread_id] = list of messages
_threads: dict[str, list] = defaultdict(list)
# message index: message_id → message
_messages: dict[str, dict] = {}

# ── Pydantic 모델 ─────────────────────────────────────────────

class AgentRef(BaseModel):
    agent_id: str
    display_name: Optional[str] = None


class A2ATask(BaseModel):
    type: str = "message"            # message / analyze / execute / review / delegate
    content: str
    context: dict = Field(default_factory=dict)
    priority: str = "normal"         # urgent / high / normal / low
    attachments: list[str] = Field(default_factory=list)


class A2AMessage(BaseModel):
    """에이전트 간 메시지 전송 요청"""
    from_agent: AgentRef = Field(alias="from")
    to_agent: AgentRef = Field(alias="to")
    task: A2ATask
    reply_to: Optional[str] = None   # in_reply_to message_id
    thread_id: Optional[str] = None  # 기존 스레드에 추가할 경우

    model_config = {"populate_by_name": True}


class A2ABroadcast(BaseModel):
    """전체 에이전트 브로드캐스트"""
    from_agent: AgentRef = Field(alias="from")
    task: A2ATask
    exclude: list[str] = Field(default_factory=list)  # 제외할 agent_id 목록

    model_config = {"populate_by_name": True}


class A2AResponse(BaseModel):
    """A2A 메시지 응답 (에이전트가 처리 후 반환)"""
    in_reply_to: str
    from_agent: AgentRef = Field(alias="from")
    status: str = "completed"        # completed / processing / failed / delegated
    content: str
    confidence: Optional[float] = None
    thread_id: Optional[str] = None

    model_config = {"populate_by_name": True}


# ── 유틸리티 ─────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_message_envelope(
    from_agent: AgentRef,
    to_agent: Optional[AgentRef],
    task: A2ATask,
    reply_to: Optional[str] = None,
    thread_id: Optional[str] = None,
    broadcast: bool = False,
) -> dict:
    message_id = f"msg-{uuid.uuid4().hex[:8]}"
    tid = thread_id or f"thread-{uuid.uuid4().hex[:6]}"

    envelope = {
        "a2a_version": A2A_VERSION,
        "message_id": message_id,
        "timestamp": _now_iso(),
        "from": {
            "agent_id": from_agent.agent_id,
            "display_name": from_agent.display_name or from_agent.agent_id,
        },
        "task": {
            "type": task.type,
            "content": task.content,
            "context": task.context,
            "priority": task.priority,
            "attachments": task.attachments,
        },
        "reply_to": reply_to,
        "thread_id": tid,
        "broadcast": broadcast,
    }
    if to_agent:
        envelope["to"] = {
            "agent_id": to_agent.agent_id,
            "display_name": to_agent.display_name or to_agent.agent_id,
        }
    return envelope


# ── FastAPI Router ────────────────────────────────────────────────

a2a_router = APIRouter(tags=["A2A Protocol"])


@a2a_router.post("/send")
def a2a_send(msg: A2AMessage) -> dict:
    """
    에이전트 간 메시지 전송.
    수신 에이전트의 inbox에 메시지를 추가하고 thread에 기록한다.
    """
    envelope = _build_message_envelope(
        from_agent=msg.from_agent,
        to_agent=msg.to_agent,
        task=msg.task,
        reply_to=msg.reply_to,
        thread_id=msg.thread_id,
    )
    message_id = envelope["message_id"]
    thread_id = envelope["thread_id"]

    # 저장
    _messages[message_id] = envelope
    _inbox[msg.to_agent.agent_id].appendleft(envelope)
    _threads[thread_id].append(envelope)

    return {
        "status": "sent",
        "message_id": message_id,
        "thread_id": thread_id,
        "to": msg.to_agent.agent_id,
        "timestamp": envelope["timestamp"],
    }


@a2a_router.get("/inbox/{agent_id}")
def a2a_inbox(agent_id: str, limit: int = 20, unread_only: bool = False) -> dict:
    """
    에이전트 수신함 조회.
    최신 메시지가 먼저 오도록 반환한다.
    """
    messages = list(_inbox.get(agent_id, []))[:limit]
    return {
        "agent_id": agent_id,
        "message_count": len(messages),
        "messages": messages,
        "timestamp": _now_iso(),
    }


@a2a_router.get("/thread/{thread_id}")
def a2a_thread(thread_id: str) -> dict:
    """스레드 전체 대화 조회 (시간순)"""
    messages = _threads.get(thread_id, [])
    if not messages:
        raise HTTPException(status_code=404, detail=f"Thread not found: {thread_id}")
    return {
        "thread_id": thread_id,
        "message_count": len(messages),
        "messages": messages,
        "participants": list({
            m["from"]["agent_id"] for m in messages
        }),
        "created_at": messages[0]["timestamp"] if messages else None,
        "last_activity": messages[-1]["timestamp"] if messages else None,
    }


@a2a_router.post("/broadcast")
def a2a_broadcast(req: A2ABroadcast) -> dict:
    """
    전체 에이전트에게 동일 메시지 브로드캐스트.
    exclude 목록의 에이전트는 제외한다.
    """
    from agent_gateway import REGISTERED_AGENTS  # 순환 방지용 지연 import

    envelope_base = _build_message_envelope(
        from_agent=req.from_agent,
        to_agent=None,
        task=req.task,
        broadcast=True,
    )
    thread_id = envelope_base["thread_id"]
    recipients = []

    for agent_id in REGISTERED_AGENTS:
        if agent_id in req.exclude:
            continue
        if agent_id == req.from_agent.agent_id:
            continue  # 자기 자신 제외

        msg_copy = {
            **envelope_base,
            "message_id": f"msg-{uuid.uuid4().hex[:8]}",
            "to": {"agent_id": agent_id},
        }
        _messages[msg_copy["message_id"]] = msg_copy
        _inbox[agent_id].appendleft(msg_copy)
        _threads[thread_id].append(msg_copy)
        recipients.append(agent_id)

    return {
        "status": "broadcast_sent",
        "thread_id": thread_id,
        "recipients": recipients,
        "count": len(recipients),
        "timestamp": _now_iso(),
    }


@a2a_router.post("/respond")
def a2a_respond(resp: A2AResponse) -> dict:
    """
    에이전트가 받은 메시지에 응답.
    원본 메시지 발신자의 inbox에 응답을 추가한다.
    """
    original = _messages.get(resp.in_reply_to)
    if not original:
        raise HTTPException(status_code=404, detail=f"Original message not found: {resp.in_reply_to}")

    original_sender_id = original["from"]["agent_id"]
    thread_id = resp.thread_id or original.get("thread_id", f"thread-{uuid.uuid4().hex[:6]}")

    response_envelope = {
        "a2a_version": A2A_VERSION,
        "message_id": f"msg-{uuid.uuid4().hex[:8]}",
        "timestamp": _now_iso(),
        "in_reply_to": resp.in_reply_to,
        "thread_id": thread_id,
        "from": {
            "agent_id": resp.from_agent.agent_id,
            "display_name": resp.from_agent.display_name,
        },
        "to": {"agent_id": original_sender_id},
        "response": {
            "status": resp.status,
            "content": resp.content,
            "confidence": resp.confidence,
        },
    }
    _messages[response_envelope["message_id"]] = response_envelope
    _inbox[original_sender_id].appendleft(response_envelope)
    _threads[thread_id].append(response_envelope)

    return {
        "status": "response_sent",
        "message_id": response_envelope["message_id"],
        "thread_id": thread_id,
        "to": original_sender_id,
        "timestamp": response_envelope["timestamp"],
    }


@a2a_router.get("/status")
def a2a_status() -> dict:
    """A2A 프로토콜 상태 및 통계"""
    total_inbox = sum(len(v) for v in _inbox.values())
    return {
        "a2a_version": A2A_VERSION,
        "status": "active",
        "stats": {
            "total_messages": len(_messages),
            "total_threads": len(_threads),
            "active_inboxes": len(_inbox),
            "total_inbox_items": total_inbox,
        },
        "agents_with_messages": list(_inbox.keys()),
        "timestamp": _now_iso(),
    }


# ── Python 직접 호출용 유틸 (socketio_server.py 에서 사용) ───────

def send_a2a_message(
    from_id: str,
    to_id: str,
    content: str,
    task_type: str = "message",
    thread_id: Optional[str] = None,
    from_name: Optional[str] = None,
    to_name: Optional[str] = None,
) -> dict:
    """
    socketio_server.py 등 내부 코드에서 직접 호출하는 간편 함수.
    HTTP 요청 없이 인메모리 큐에 직접 추가한다.
    """
    msg = A2AMessage.model_validate({
        "from": {"agent_id": from_id, "display_name": from_name},
        "to": {"agent_id": to_id, "display_name": to_name},
        "task": {"type": task_type, "content": content},
        "thread_id": thread_id,
    })
    envelope = _build_message_envelope(
        from_agent=msg.from_agent,
        to_agent=msg.to_agent,
        task=msg.task,
        thread_id=thread_id,
    )
    _messages[envelope["message_id"]] = envelope
    _inbox[to_id].appendleft(envelope)
    _threads[envelope["thread_id"]].append(envelope)
    return envelope


def get_inbox(agent_id: str, limit: int = 10) -> list[dict]:
    """에이전트 수신함 조회 (내부 호출용)"""
    return list(_inbox.get(agent_id, []))[:limit]
