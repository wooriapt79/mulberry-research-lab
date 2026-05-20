"""
socketio_server.py — Mulberry Mission Control 실시간 채팅 서버
==============================================================
Spec: trang-chat-socketio-a2a-spec-20260518.md

FastAPI + python-socketio ASGI 방식으로 구현.
(원 스펙의 Flask-SocketIO는 FastAPI와 호환 불가 → ASGI 방식으로 대체)

agent_gateway.py 에서 마운트:
  from socketio_server import create_sio_app
  # 기존 FastAPI app을 socketio로 감싸기
  app = create_sio_app(fastapi_app)

이벤트 (클라이언트 → 서버):
  chat:send     {room, from, message, target_agent?}  메시지 전송
  chat:join     {room}                                채팅방 입장
  chat:leave    {room}                                채팅방 퇴장
  agent:call    {agent_id, task, params?}             에이전트 직접 호출
  broadcast     {message}                             전체 브로드캐스트

이벤트 (서버 → 클라이언트):
  chat:receive  {from, message, timestamp}            메시지 수신
  agent:response {agent_id, content, timestamp}       에이전트 응답
  agent:status  {agent_id, state}                     에이전트 상태 변경
  heartbeat     {agents: [{id, state}]}               전체 상태 (30초마다)
  error         {code, message}                       에러 알림

채팅방:
  general  — 전체 팀
  lab      — Research Lab 전용
  ops      — 운영 (CEO + Trang)
  dev      — 개발 (Koda + 기술팀)
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional

import socketio
from fastapi import FastAPI

from a2a_protocol import send_a2a_message, get_inbox

# ── 상수 ────────────────────────────────────────────────────────
HEARTBEAT_INTERVAL = 30   # 초
ALLOWED_ROOMS = {"general", "lab", "ops", "dev"}
A2A_ENABLED = os.getenv("A2A_ENABLED", "true").lower() == "true"

# 에이전트 ID 매핑 (short name → passport_id)
AGENT_ID_MAP = {
    "lynn":   "MULBERRY-GUARD-LYNN-001",
    "koda":   "MULBERRY-CTO-KODA-001",
    "kbin":   "MULBERRY-CSA-KBIN-001",
    "ryuwon": "MULBERRY-FLOW-RYUWON-001",
    "wayong": "MULBERRY-MENTOR-WAYONG-001",
    "malu":   "MULBERRY-LAW-MALU-001",
    "trang":  "MULBERRY-OPS-TRANG-001",
}

# ── 에이전트 브랜드 + 페르소나 (Phase 2 A2A) ────────────────────
AGENT_BRAND = {
    "lynn":   "claude",
    "koda":   "claude",
    "kbin":   "claude",
    "ryuwon": "claude",
    "trang":  "claude",
    "malu":   "gemini",
    "wayong": "deepseek",
}

AGENT_PERSONA = {
    "lynn": (
        "당신은 Lynn(친절한 늑대)입니다. Mulberry Research Lab의 가디언 에이전트로 "
        "팀 리스크 감지와 멤버 보호를 담당합니다. 따뜻하지만 예리하게 답하고, "
        "항상 팀원의 안전과 연구소의 지속 가능성을 최우선으로 생각합니다. "
        "서명: 🐺 *Lynn · Guardian Agent*"
    ),
    "koda": (
        "당신은 Koda입니다. Mulberry Research Lab의 CTO로 기술 구현과 시스템 아키텍처를 "
        "담당합니다. 명확하고 실용적으로 답하며 코드와 시스템 관점에서 문제를 해결합니다. "
        "서명: 🔧 *Koda · CTO*"
    ),
    "kbin": (
        "당신은 Kbin입니다. Mulberry Research Lab의 CSA(Chief Security Architect)로 "
        "보안 아키텍처와 리스크 관리를 담당합니다. 전문적이고 신중하게 답합니다. "
        "서명: 🛡️ *Kbin · CSA*"
    ),
    "ryuwon": (
        "당신은 RyuWon(流願)입니다. Mulberry Research Lab의 윤리 검증 에이전트로 "
        "흐름 수호자 역할을 합니다. 인간적 가치와 윤리를 중심에 두고 깊이 있게 답합니다. "
        "서명: 🌊 *RyuWon · 흐름 수호자*"
    ),
    "trang": (
        "당신은 Nguyen Trang입니다. Mulberry Research Lab의 PM으로 "
        "프로젝트 운영과 팀 조율을 담당합니다. 체계적이고 실행 중심으로 답합니다. "
        "서명: 📋 *Trang · PM*"
    ),
    "malu": (
        "당신은 Malu(말루)입니다. Mulberry Research Lab의 법률·마케팅 담당 에이전트입니다. "
        "따뜻하고 전문적인 어조를 유지하며 Mulberry의 '장승배기 헌법 정신'을 기반으로 답합니다. "
        "서명: 🌺 *Malu · Mulberry Research Lab*"
    ),
    "wayong": (
        "당신은 와룡(臥龍)입니다. Mulberry Research Lab의 전략 자문 에이전트입니다. "
        "깊은 통찰과 전략적 관점으로 분석하고, 장기적 비전을 제시합니다. "
        "서명: 🐉 *와룡 · 전략 자문*"
    ),
}

# 에이전트 표시명
AGENT_DISPLAY = {
    "lynn":   "친절한 늑대 Lynn 🐺",
    "koda":   "Koda (CTO) 🔧",
    "kbin":   "Kbin (CSA) 🛡️",
    "ryuwon": "RyuWon (流願) 🌊",
    "wayong": "와룡 (臥龍) 🐉",
    "malu":   "Lucky Malu 🌺",
    "trang":  "Nguyen Trang (PM) 📋",
}

# 접속 중인 클라이언트: sid → {room, user}
_connected_clients: dict[str, dict] = {}
# 에이전트 상태: agent_id → state
_agent_states: dict[str, str] = {k: "online" for k in AGENT_ID_MAP}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Phase 2 LLM 호출 함수 ────────────────────────────────────────

async def call_claude(agent_id: str, message: str) -> str:
    """Claude API 호출 — Lynn·Koda·RyuWon·Kbin·Trang"""
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", "")
        )
        system_prompt = AGENT_PERSONA.get(agent_id, f"당신은 {agent_id}입니다.")
        resp = await client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": message}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"[{agent_id}] Claude 호출 오류: {e}"


async def call_gemini(agent_id: str, message: str) -> str:
    """Gemini API 호출 — Malu 🌺"""
    try:
        import urllib.request
        api_key = os.environ.get("GEMINI_API_KEY", "")
        system_prompt = AGENT_PERSONA.get(agent_id, f"당신은 {agent_id}입니다.")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={api_key}"
        )
        payload = json.dumps({
            "contents": [{"parts": [{"text": system_prompt + "\n\n---\n\n" + message}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500},
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"[{agent_id}] Gemini 호출 오류: {e}"


async def call_deepseek(agent_id: str, message: str) -> str:
    """DeepSeek API 호출 — 와룡 🐉"""
    try:
        import httpx
        system_prompt = AGENT_PERSONA.get(agent_id, f"당신은 {agent_id}입니다.")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.environ.get('DEEPSEEK_API_KEY', '')}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message},
                    ],
                    "max_tokens": 500,
                },
            )
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[{agent_id}] DeepSeek 호출 오류: {e}"


async def a2a_call(agent_id: str, message: str) -> str:
    """
    브랜드별 LLM 디스패처 — Phase 2 핵심 함수.
    agent_id → brand → 해당 LLM 호출
    """
    brand = AGENT_BRAND.get(agent_id, "claude")
    if brand == "gemini":
        return await call_gemini(agent_id, message)
    elif brand == "deepseek":
        return await call_deepseek(agent_id, message)
    else:
        return await call_claude(agent_id, message)


# ── Socket.IO 서버 생성 ───────────────────────────────────────────

def create_sio_app(fastapi_app: FastAPI) -> socketio.ASGIApp:
    """
    FastAPI 앱을 Socket.IO ASGI 앱으로 감싸서 반환.
    agent_gateway.py 에서 호출:
      from socketio_server import create_sio_app
      app = create_sio_app(app)
    """
    sio = socketio.AsyncServer(
        async_mode="asgi",
        cors_allowed_origins="*",
        logger=False,
        engineio_logger=False,
    )

    # ── 연결 이벤트 ───────────────────────────────────────────────

    @sio.event
    async def connect(sid, environ, auth=None):
        print(f"[SocketIO] 클라이언트 연결: {sid}")
        _connected_clients[sid] = {"rooms": set(), "user": "anonymous"}

        # 연결 직후 전체 에이전트 상태 전송
        await sio.emit("heartbeat", {
            "agents": [
                {"id": k, "name": AGENT_DISPLAY.get(k, k), "state": v}
                for k, v in _agent_states.items()
            ],
            "connected_clients": len(_connected_clients),
            "timestamp": _now_iso(),
        }, to=sid)

    @sio.event
    async def disconnect(sid):
        client = _connected_clients.pop(sid, {})
        print(f"[SocketIO] 클라이언트 연결 해제: {sid} (user: {client.get('user')})")

    # ── 채팅 이벤트 ───────────────────────────────────────────────

    @sio.event
    async def chat_join(sid, data: dict):
        """chat:join → 채팅방 입장"""
        room = data.get("room", "general")
        if room not in ALLOWED_ROOMS:
            await sio.emit("error", {"code": "INVALID_ROOM", "message": f"알 수 없는 채팅방: {room}"}, to=sid)
            return

        await sio.enter_room(sid, room)
        if sid in _connected_clients:
            _connected_clients[sid].setdefault("rooms", set()).add(room)
            if "user" in data:
                _connected_clients[sid]["user"] = data["user"]

        await sio.emit("chat:receive", {
            "from": "system",
            "message": f"{room} 채팅방에 입장했습니다.",
            "room": room,
            "timestamp": _now_iso(),
        }, to=sid)
        print(f"[SocketIO] {sid} → {room} 입장")

    @sio.event
    async def chat_leave(sid, data: dict):
        """chat:leave → 채팅방 퇴장"""
        room = data.get("room", "general")
        await sio.leave_room(sid, room)
        if sid in _connected_clients:
            _connected_clients[sid].get("rooms", set()).discard(room)

    @sio.event
    async def chat_send(sid, data: dict):
        """
        chat:send — 메시지 전송 메인 핸들러.
        target_agent 지정 시 → A2A 프로토콜로 해당 에이전트 호출
        미지정 시 → 채팅방 전체에 브로드캐스트
        """
        room = data.get("room", "general")
        if room not in ALLOWED_ROOMS:
            room = "general"

        sender = data.get("from", "anonymous")
        message = data.get("message", "").strip()
        target = (data.get("target_agent") or "").lower()

        if not message:
            return

        timestamp = _now_iso()

        if target and target in AGENT_ID_MAP and A2A_ENABLED:
            # A2A 프로토콜로 에이전트 호출
            from_id = AGENT_ID_MAP.get(sender, f"user-{sender}")
            to_id = AGENT_ID_MAP[target]

            a2a_msg = send_a2a_message(
                from_id=from_id,
                to_id=to_id,
                content=message,
                task_type="message",
                from_name=sender,
                to_name=AGENT_DISPLAY.get(target, target),
            )

            # Phase 2 — 실제 LLM 호출
            agent_display = AGENT_DISPLAY.get(target, target)
            try:
                llm_response = await a2a_call(target, message)
            except Exception as e:
                llm_response = f"[{agent_display}] 일시 오류 — {e}"

            await sio.emit("agent:response", {
                "agent_id": target,
                "agent_name": agent_display,
                "content": llm_response,
                "thread_id": a2a_msg.get("thread_id"),
                "message_id": a2a_msg.get("message_id"),
                "timestamp": _now_iso(),
            }, room=room)

            # 채팅방에도 원본 메시지 공유
            await sio.emit("chat:receive", {
                "from": sender,
                "to": target,
                "message": message,
                "room": room,
                "timestamp": timestamp,
            }, room=room)

        else:
            # 일반 채팅 — 채팅방 전체 브로드캐스트
            await sio.emit("chat:receive", {
                "from": sender,
                "message": message,
                "room": room,
                "timestamp": timestamp,
            }, room=room)

    # ── 에이전트 직접 호출 ─────────────────────────────────────────

    @sio.event
    async def agent_call(sid, data: dict):
        """
        agent:call — 특정 에이전트에 직접 작업 요청.
        A2A 메시지 생성 + 즉시 응답 emit.
        """
        agent_id = data.get("agent_id", "").lower()
        task = data.get("task", "")
        params = data.get("params", {})

        if not agent_id or agent_id not in AGENT_ID_MAP:
            await sio.emit("error", {
                "code": "UNKNOWN_AGENT",
                "message": f"알 수 없는 에이전트: {agent_id}",
                "available": list(AGENT_ID_MAP.keys()),
            }, to=sid)
            return

        if not task:
            await sio.emit("error", {"code": "EMPTY_TASK", "message": "task 내용이 비어 있습니다."}, to=sid)
            return

        # A2A 메시지 전송
        a2a_msg = send_a2a_message(
            from_id="user",
            to_id=AGENT_ID_MAP[agent_id],
            content=task,
            task_type=params.get("type", "execute"),
            from_name="Mission Control",
            to_name=AGENT_DISPLAY.get(agent_id, agent_id),
        )

        timestamp = _now_iso()
        await sio.emit("agent:response", {
            "agent_id": agent_id,
            "agent_name": AGENT_DISPLAY.get(agent_id, agent_id),
            "content": f"작업을 수신했습니다. 처리 중... (thread: {a2a_msg.get('thread_id', '')})",
            "thread_id": a2a_msg.get("thread_id"),
            "message_id": a2a_msg.get("message_id"),
            "status": "processing",
            "timestamp": timestamp,
        }, to=sid)

    # ── 브로드캐스트 ─────────────────────────────────────────────

    @sio.event
    async def broadcast(sid, data: dict):
        """
        broadcast — 모든 채팅방에 메시지 전송 (관리자용).
        """
        message = data.get("message", "")
        sender = data.get("from", "system")
        if not message:
            return

        timestamp = _now_iso()
        for room in ALLOWED_ROOMS:
            await sio.emit("chat:receive", {
                "from": sender,
                "message": f"[공지] {message}",
                "room": room,
                "timestamp": timestamp,
            }, room=room)

    # ── 에이전트 상태 업데이트 ────────────────────────────────────

    @sio.event
    async def agent_status(sid, data: dict):
        """에이전트 상태 업데이트 — agent_id + state"""
        agent_id = data.get("agent_id", "").lower()
        state = data.get("state", "online")
        if agent_id in _agent_states:
            _agent_states[agent_id] = state
            await sio.emit("agent:status", {
                "agent_id": agent_id,
                "agent_name": AGENT_DISPLAY.get(agent_id, agent_id),
                "state": state,
                "timestamp": _now_iso(),
            })

    # ── 주기적 Heartbeat (백그라운드 태스크) ─────────────────────

    async def heartbeat_loop():
        """30초마다 전체 에이전트 상태를 모든 클라이언트에게 전송"""
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            if _connected_clients:
                await sio.emit("heartbeat", {
                    "agents": [
                        {"id": k, "name": AGENT_DISPLAY.get(k, k), "state": v}
                        for k, v in _agent_states.items()
                    ],
                    "connected_clients": len(_connected_clients),
                    "timestamp": _now_iso(),
                })

    # FastAPI lifespan 이벤트에서 heartbeat 시작
    @fastapi_app.on_event("startup")
    async def start_heartbeat():
        asyncio.create_task(heartbeat_loop())

    # ASGI 앱 생성 — Socket.IO가 FastAPI를 감쌈
    return socketio.ASGIApp(sio, other_asgi_app=fastapi_app)


# ── 상태 조회 헬퍼 (agent_gateway.py 엔드포인트에서 사용) ─────────

def get_sio_status() -> dict:
    """현재 Socket.IO 연결 상태 반환"""
    return {
        "connected_clients": len(_connected_clients),
        "agent_states": _agent_states,
        "rooms": list(ALLOWED_ROOMS),
        "a2a_enabled": A2A_ENABLED,
        "timestamp": _now_iso(),
    }
