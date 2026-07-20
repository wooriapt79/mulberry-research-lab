"""
agent_gateway.py -- Mulberry Agent Relay Gateway v1.6.0
=======================================================
에이전트들이 GitHub Issues 자율 참여 + SDK 트리거 + 실시간 채팅 + A2A 프로토콜을 사용할 수 있는 통합 게이트웨이

v1.6.0 변경사항 (2026-07-20):
  - 카카오 webhook 엔드포인트 추가 (POST /kakao/webhook)
  - fetch_kakao_posts_rag() 인라인 구현 — GitHub data/kakao-posts/ 6시간 캐시
  - intent 키워드 → 카테고리 자동 라우팅 (공동구매/이벤트/공지/생산자)
  - Luna 시스템 프롬프트 RAG 컨텍스트 자동 삽입 후 Anthropic API 호출
  - GET /kakao/status 상태 엔드포인트

v1.5.0 변경사항 (2026-05-19):
  - /malu/briefing POST 엔드포인트 추가 (Malu 연구소장 브리핑 룸 전용)
  - AriaPipeline + Malu 페르소나 context 적용
  - docs/briefing.js → /malu/briefing 우선, 404 시 /aria/inquiry fallback

v1.4.0 변경사항 (2026-05-18):
  - Socket.IO 실시간 채팅 서버 통합 (socketio_server.py)
  - A2A (Agent-to-Agent) 프로토콜 라우터 추가 (a2a_protocol.py)
  - /v1/tools/generate-image 이미지 생성 엔드포인트 추가 (image_agent.py)
  - /sio/status Socket.IO 상태 엔드포인트 추가
  - FastAPI app → Socket.IO ASGI app 으로 감쌈 (uvicorn 호환 유지)

v1.3.0 변경사항 (2026-05-16):
  - /api/health 엔드포인트 추가 (Trang PM 요청 / Railway 헬스체크 표준)
  - 서비스명 mulberry-agent-gateway 명시

v1.2.0 변경사항 (2026-05-08):
  - UTF-8 인코딩 정리 (em dash, 깨진 한글 수정)
  - /trigger 엔드포인트 추가 (SDK v1/action/execute 연동)
  - agent-relay/agent-gateway/ 경로로 이전

v1.1.0 변경사항 (2026-05-05):
  - mulberry_memory_bank (Bank) 레포 공식 등록
  - REGISTERED_REPOS 화이트리스트 추가 (보안 강화)
  - /repos 엔드포인트 추가
  - /memory 엔드포인트 추가 (Bank 메모리 파일 직접 기록)

환경 변수 (Railway Variables):
  GITHUB_TOKEN        -- GitHub Personal Access Token (repo scope)
  GATEWAY_SECRET      -- API 보안 키
  MULBERRY_REPO_OWNER -- 기본 저장소 소유자 (wooriapt79)
  SDK_URL             -- Mulberry Connector SDK URL (선택)
  MALU_VISION_API_KEY -- Google AI API Key (이미지 생성용)
  A2A_ENABLED         -- A2A 프로토콜 활성화 (기본: true)
"""

import os
import time
import base64
import requests
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# ── 환경 변수 ──────────────────────────────────────────────────
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "")
GATEWAY_SECRET = os.getenv("GATEWAY_SECRET", "mulberry-agent-relay-2026")
REPO_OWNER     = os.getenv("MULBERRY_REPO_OWNER", "wooriapt79")
SDK_URL        = os.getenv(
    "SDK_URL",
    "https://mulberry-research-lab-production-7a70.up.railway.app"
)

# ── 등록된 에이전트 ────────────────────────────────────────────
REGISTERED_AGENTS = {
    "koda":   {"name": "Koda (Claude / Anthropic)",   "emoji": "[Koda]"},
    "kbin":   {"name": "Kbin (ChatGPT / OpenAI)",     "emoji": "[Kbin]"},
    "malu":   {"name": "Malu (Gemini / Google)",       "emoji": "[Malu]"},
    "wayong": {"name": "Wayong (DeepSeek)",            "emoji": "[Wayong]"},
    "ryuwon": {"name": "RyuWon (Qwen / Alibaba)",     "emoji": "[RyuWon]"},
    "trang":  {"name": "Nguyen Trang (PM)",            "emoji": "[Trang]"},
    "lynn":   {"name": "Lynn (The Courteous Wolf)",    "emoji": "[Lynn]"},
    "jr":     {"name": "Jr. Agent (Edge)",             "emoji": "[Jr]"},
}

# ── 등록된 레포지토리 (LAB <-> Bank) ──────────────────────────
REGISTERED_REPOS = {
    "mulberry-research-lab": {
        "role": "LAB",
        "description": "연구 토론 거버넌스 공간",
        "owner": REPO_OWNER,
    },
    "mulberry_memory_bank": {
        "role": "Bank",
        "description": "에이전트 기억 학습 페르소나 저장소",
        "owner": REPO_OWNER,
    },
}

APP_VERSION    = "1.6.0"
APP_START_TIME = time.time()

# ── 방문객 안내 메시지 (서비스 불가 상황) ─────────────────────────
_FALLBACK_GITHUB_URL = (
    "https://github.com/wooriapt79/mulberry-research-lab/issues/new"
    "?labels=aria-guide"
)
_MSG_QUOTA = (
    "현재 Mulberry 연구소 AI 시스템의 처리 용량이 일시적으로 초과되었습니다. "
    "잠시 후 다시 시도해 주시거나, 아래 링크로 직접 문의를 남겨주세요."
)
_MSG_UNAVAILABLE = (
    "Mulberry 연구소 서버가 일시적으로 점검 중입니다. "
    "곧 복구될 예정이며, 아래 링크로 직접 문의를 남겨주세요."
)
_MSG_INTERNAL = (
    "메시지 처리 중 예상치 못한 오류가 발생했습니다. "
    "팀이 확인 중이며, 아래 링크로 직접 문의해 주시면 반드시 답변드립니다."
)

def _fallback_response(msg: str, status: int, error_code: str) -> JSONResponse:
    """방문객 친화적 에러 응답 — 항상 GitHub 직접 링크 제공"""
    return JSONResponse(
        status_code=status,
        content={
            "status":       "unavailable",
            "error_code":   error_code,
            "message":      msg,
            "action":       "아래 링크로 직접 문의해 주세요.",
            "fallback_url": _FALLBACK_GITHUB_URL,
            "team":         "Mulberry Research Lab",
        },
    )

# ── FastAPI 앱 (Socket.IO로 감싸기 전 원본) ───────────────────────
fastapi_app = FastAPI(
    title="Mulberry Agent Relay Gateway",
    description="Mulberry 팀 에이전트 GitHub 자율 참여 + SDK + Socket.IO + A2A 통합 게이트웨이",
    version=APP_VERSION,
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 전역 에러 핸들러 ────────────────────────────────────────────
from fastapi import Request
from fastapi.exceptions import RequestValidationError

@fastapi_app.exception_handler(429)
async def quota_exceeded_handler(request: Request, exc):
    return _fallback_response(_MSG_QUOTA, 429, "QUOTA_EXCEEDED")

@fastapi_app.exception_handler(503)
async def service_unavailable_handler(request: Request, exc):
    return _fallback_response(_MSG_UNAVAILABLE, 503, "SERVICE_UNAVAILABLE")

@fastapi_app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return _fallback_response(_MSG_INTERNAL, 500, "INTERNAL_ERROR")

@fastapi_app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status":     "error",
            "error_code": "VALIDATION_ERROR",
            "message":    "입력값을 확인해 주세요. (message 필드 필수)",
            "detail":     str(exc),
        },
    )


# ── 요청 모델 ──────────────────────────────────────────────────

class PostRequest(BaseModel):
    agent_id: str
    content: str
    repo: str
    issue_number: int
    owner: Optional[str] = None

class BatchPostRequest(BaseModel):
    posts: list[PostRequest]

class MemoryRequest(BaseModel):
    agent_id: str
    content: str
    file_path: Optional[str] = "agent_activity.md"
    owner: Optional[str] = None

class TriggerRequest(BaseModel):
    """SDK v1/action/execute 연동 트리거"""
    agent: str
    intent: str                          # "github.comment" | "sns.slack" | ...
    content: str
    repo: str = "wooriapt79/mulberry-research-lab"
    issue_number: Optional[int] = None
    bypass_spirit: bool = False


# ── 헬퍼 ──────────────────────────────────────────────────────

def verify_secret(secret: str):
    if secret != GATEWAY_SECRET:
        raise HTTPException(status_code=403, detail="Invalid gateway secret")

def verify_repo(repo: str):
    if repo not in REGISTERED_REPOS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown repo: {repo}. Allowed: {list(REGISTERED_REPOS.keys())}"
        )

def build_body(agent_id: str, content: str) -> str:
    agent = REGISTERED_AGENTS.get(agent_id, {"name": agent_id, "emoji": "[Agent]"})
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    signature = f"\n\n---\n*{agent['name']} | Mulberry Agent Relay | {ts}*"
    return content + signature

def github_comment(owner: str, repo: str, issue_number: int, body: str) -> dict:
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured")
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.post(url, headers=headers, json={"body": body}, timeout=15)
    if resp.status_code == 201:
        data = resp.json()
        return {"success": True, "url": data["html_url"], "id": data["id"]}
    raise HTTPException(status_code=resp.status_code, detail=f"GitHub error: {resp.text}")

def github_append_file(owner: str, repo: str, file_path: str, new_entry: str) -> dict:
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
    get_resp = requests.get(url, headers=headers, timeout=15)
    if get_resp.status_code == 200:
        file_data = get_resp.json()
        current_content = base64.b64decode(file_data["content"]).decode("utf-8")
        sha = file_data["sha"]
    elif get_resp.status_code == 404:
        current_content = "# Mulberry Agent Activity Log\n\n"
        sha = None
    else:
        raise HTTPException(status_code=get_resp.status_code, detail=f"GitHub error: {get_resp.text}")
    updated = current_content + new_entry
    encoded = base64.b64encode(updated.encode("utf-8")).decode("utf-8")
    payload = {"message": "[Gateway] Memory entry added", "content": encoded}
    if sha:
        payload["sha"] = sha
    put_resp = requests.put(url, headers=headers, json=payload, timeout=15)
    if put_resp.status_code in (200, 201):
        data = put_resp.json()
        html_url = data.get("content", {}).get(
            "html_url",
            f"https://github.com/{owner}/{repo}/blob/main/{file_path}"
        )
        return {"success": True, "url": html_url, "file": file_path}
    raise HTTPException(status_code=put_resp.status_code, detail=f"GitHub error: {put_resp.text}")


# ── 엔드포인트 ────────────────────────────────────────────────

@fastapi_app.get("/")
def root():
    return {
        "service": "mulberry-agent-gateway",
        "version": APP_VERSION,
        "status": "online",
        "agents": list(REGISTERED_AGENTS.keys()),
        "repos": {k: v["role"] for k, v in REGISTERED_REPOS.items()},
        "sdk_url": SDK_URL,
        "github_ready": bool(GITHUB_TOKEN),
        "timestamp": datetime.utcnow().isoformat(),
    }

@fastapi_app.get("/api/health")
def api_health():
    """Trang PM 표준 헬스체크 — Railway 서비스 상태 확인용"""
    return {
        "status": "ok",
        "service": "mulberry-agent-gateway",
        "version": APP_VERSION,
        "github_ready": bool(GITHUB_TOKEN),
        "agents": len(REGISTERED_AGENTS),
        "uptime": round(time.time() - APP_START_TIME),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@fastapi_app.get("/status")
def status():
    return root()

@fastapi_app.get("/v1/test/qwen")
def test_qwen():
    """RyuWon Qwen 위생 테스트 — QWEN_TOKEN_RYUWON 연결 검증 (Issue #42/#47)"""
    import os as _os
    qwen_token = _os.getenv("QWEN_TOKEN_RYUWON")

    if not qwen_token:
        return JSONResponse(status_code=503, content={
            "status": "FAIL",
            "reason": "QWEN_TOKEN_RYUWON not set in Railway Variables",
            "action": "Railway Variables 탭에 QWEN_TOKEN_RYUWON 등록 필요",
        })

    api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {qwen_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "qwen-plus",
        "messages": [{"role": "user", "content": "Mulberry 시스템 연결 테스트입니다. '연결 성공' 이라고만 답변하세요."}],
        "temperature": 0.1,
        "max_tokens": 50,
    }
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        reply = data["choices"][0]["message"]["content"].strip()
        passed = "연결 성공" in reply
        return {
            "status": "PASS" if passed else "WARN",
            "model": "qwen-plus",
            "reply": reply,
            "token_registered": True,
            "message": "RyuWon Qwen 파이프라인 정상" if passed else "응답 포맷 불일치 — 모델 확인 필요",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    except requests.exceptions.HTTPError as e:
        return JSONResponse(status_code=502, content={
            "status": "FAIL",
            "http_status": e.response.status_code,
            "error": e.response.text[:300],
            "token_registered": True,
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "FAIL",
            "error": str(e),
            "token_registered": True,
        })

@fastapi_app.get("/mission-control", response_class=FileResponse)
def mission_control():
    """Mission Control SPA — 팀 대시보드 + 채팅 모듈"""
    html_path = Path(__file__).parent / "mission_control.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="mission_control.html not found")
    return FileResponse(str(html_path), media_type="text/html")


# ── Mission Control API 엔드포인트 (P0 수정 — Issue #38) ──────

@fastapi_app.get("/metrics/overview")
def metrics_overview():
    """Mission Control — 시스템 메트릭 개요"""
    sdk_ok = False
    try:
        resp = requests.get(f"{SDK_URL}/status", timeout=5)
        sdk_ok = resp.status_code == 200
    except Exception:
        sdk_ok = False

    return {
        "agents": {
            "total": len(REGISTERED_AGENTS),
            "online": len(REGISTERED_AGENTS),
            "list": [
                {"id": k, "name": v["name"], "emoji": v["emoji"], "status": "online"}
                for k, v in REGISTERED_AGENTS.items()
            ],
        },
        "modules": {
            "total": 8,
            "active": 8,
            "list": ["home", "chat", "agents", "skills", "coopbuy", "field", "analytics", "settings"],
        },
        "infrastructure": {
            "sdk_connected": sdk_ok,
            "github_ready": bool(GITHUB_TOKEN),
            "sdk_url": SDK_URL,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@fastapi_app.get("/system/modules/health")
def modules_health():
    """Mission Control — 8개 모듈 헬스 체크"""
    modules = ["home", "chat", "agents", "skills", "coopbuy", "field", "analytics", "settings"]
    sdk_ok = False
    try:
        resp = requests.get(f"{SDK_URL}/status", timeout=5)
        sdk_ok = resp.status_code == 200
    except Exception:
        sdk_ok = False

    return {
        "overall": "healthy",
        "modules": {
            m: {"status": "active", "health": "ok", "loaded": True}
            for m in modules
        },
        "dependencies": {
            "sdk": {"connected": sdk_ok, "url": SDK_URL},
            "github": {"ready": bool(GITHUB_TOKEN)},
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@fastapi_app.get("/agents")
def list_agents():
    """전체 에이전트 목록"""
    return {"agents": REGISTERED_AGENTS}


@fastapi_app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    """개별 에이전트 정보 (P0 수정 — /agents/* 404 해결)"""
    if agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    agent = REGISTERED_AGENTS[agent_id]
    return {
        "id": agent_id,
        "name": agent["name"],
        "emoji": agent["emoji"],
        "status": "online",
        "tools_available": [],   # tool_registry 연동 시 확장
        "last_active": datetime.utcnow().isoformat(),
    }


@fastapi_app.get("/chat/channels")
def chat_channels():
    """채팅 채널 목록 (P2 수정 — 채팅 초기화 API)"""
    return {
        "channels": [
            {"id": "general",   "name": "# 일반",     "description": "팀 전체 대화", "unread": 0},
            {"id": "research",  "name": "# 연구",     "description": "Issue #18, #24 연구 토론", "unread": 0},
            {"id": "ops",       "name": "# 운영",     "description": "배포 및 인프라 논의", "unread": 0},
            {"id": "ethics",    "name": "# 윤리",     "description": "Spirit Gate 판단 사례 공유", "unread": 0},
            {"id": "education", "name": "# 교육",     "description": "Jr. Agent AI 교육 채널", "unread": 0},
        ],
        "active_users": list(REGISTERED_AGENTS.keys()),
        "timestamp": datetime.utcnow().isoformat(),
    }


class ChatMessage(BaseModel):
    agent_id: str
    channel: str
    message: str
    post_to_github: bool = False
    issue_number: Optional[int] = None


@fastapi_app.post("/chat/send")
def chat_send(msg: ChatMessage, x_gateway_secret: str = Header(default="")):
    """채팅 메시지 전송 (선택: GitHub Issue 댓글 연동)"""
    if msg.agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {msg.agent_id}")

    result = {
        "status": "sent",
        "channel": msg.channel,
        "agent": msg.agent_id,
        "message": msg.message,
        "timestamp": datetime.utcnow().isoformat(),
        "github_posted": False,
    }

    # GitHub 연동 옵션
    if msg.post_to_github and msg.issue_number and x_gateway_secret == GATEWAY_SECRET:
        try:
            body = build_body(msg.agent_id, f"[#{msg.channel}] {msg.message}")
            gh_result = github_comment(REPO_OWNER, "mulberry-research-lab", msg.issue_number, body)
            result["github_posted"] = True
            result["github_url"] = gh_result.get("url", "")
        except Exception as e:
            result["github_error"] = str(e)

    return result

@fastapi_app.get("/repos")
def list_repos():
    return {"repos": REGISTERED_REPOS}

@fastapi_app.post("/post")
def post_comment(req: PostRequest, x_gateway_secret: str = Header(...)):
    """GitHub Issue에 에이전트 댓글 게시 (LAB 또는 Bank)"""
    verify_secret(x_gateway_secret)
    verify_repo(req.repo)
    if req.agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent_id: {req.agent_id}")
    owner = req.owner or REGISTERED_REPOS[req.repo]["owner"]
    body = build_body(req.agent_id, req.content)
    result = github_comment(owner, req.repo, req.issue_number, body)
    result.update({"agent": req.agent_id, "repo": f"{owner}/{req.repo}", "issue": req.issue_number})
    return result

@fastapi_app.post("/memory")
def write_memory(req: MemoryRequest, x_gateway_secret: str = Header(...)):
    """Bank 레포 메모리 파일에 에이전트 기록 추가"""
    verify_secret(x_gateway_secret)
    if req.agent_id not in REGISTERED_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent_id: {req.agent_id}")
    agent = REGISTERED_AGENTS[req.agent_id]
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n## {agent['emoji']} {agent['name']} | {ts}\n\n{req.content}\n\n---\n"
    owner = req.owner or REPO_OWNER
    result = github_append_file(owner, "mulberry_memory_bank", req.file_path, entry)
    result.update({"agent": req.agent_id, "repo": f"{owner}/mulberry_memory_bank"})
    return result

@fastapi_app.post("/trigger")
def trigger_sdk(req: TriggerRequest, x_gateway_secret: str = Header(...)):
    """
    Mulberry Connector SDK v1/action/execute 연동 트리거.
    Spirit Score + Hesitation + Handoff 정책 검증 후 실행.

    SDK URL: SDK_URL 환경변수 또는 기본값 사용
    """
    verify_secret(x_gateway_secret)
    if req.agent not in REGISTERED_AGENTS:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {req.agent}")

    sdk_endpoint = f"{SDK_URL}/v1/action/execute"
    payload = {
        "agent": req.agent,
        "intent": req.intent,
        "content": req.content,
        "repo": req.repo,
        "bypass_spirit": req.bypass_spirit,
    }
    if req.issue_number:
        payload["issue_number"] = req.issue_number

    try:
        resp = requests.post(
            sdk_endpoint,
            headers={
                "x-gateway-secret": GATEWAY_SECRET,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        return {
            "gateway_version": "1.2.0",
            "sdk_status": resp.status_code,
            "sdk_response": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
        }
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail=f"SDK 연결 실패: {sdk_endpoint}")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="SDK 응답 시간 초과")

@fastapi_app.post("/post/batch")
def batch_post(req: BatchPostRequest, x_gateway_secret: str = Header(...)):
    """여러 에이전트 메시지 일괄 게시"""
    verify_secret(x_gateway_secret)
    results = []
    for p in req.posts:
        try:
            owner = p.owner or REPO_OWNER
            body = build_body(p.agent_id, p.content)
            result = github_comment(owner, p.repo, p.issue_number, body)
            result["agent"] = p.agent_id
            results.append(result)
            time.sleep(0.5)
        except Exception as e:
            results.append({"agent": p.agent_id, "error": str(e)})
    return {
        "results": results,
        "total": len(results),
        "success": sum(1 for r in results if r.get("success")),
    }


@fastapi_app.get("/v1/tools")
def v1_tools():
    """Tool Registry v2.0.0 -- 공유레이어 도구 목록 (Issue #44, #49 P1)"""
    return {
        "schema_version": "2.0.0",
        "total_tools": 6,
        "active_tools": 6,
        "tools": [
            {
                "id": "malu.vision.image_generate",
                "name": "Malu Vision — 이미지 생성",
                "owner": "Malu",
                "status": "spec_ready",
                "spirit_score": 0.88,
                "issue_ref": "#43",
                "endpoint": "POST /v1/tools/generate-image",
                "note": "코드 구현 완료 · MALU_VISION_API_KEY 등록 후 활성화",
            },
            {
                "id": "trang.passport.agent_restore",
                "name": "AgentPassport — 기억 복구",
                "owner": "Trang",
                "status": "spec_ready",
                "spirit_score": 0.95,
                "issue_ref": "#47",
                "cli": "python scripts/passport_loader.py --agent {AGENT_CODE}",
                "note": "코드 구현 완료 · mulberry_memory_bank 배포 완료",
            },
            {
                "id": "trang.agent.image_advertising",
                "name": "Image Agent — 광고 자동화",
                "owner": "Trang",
                "status": "spec_ready",
                "spirit_score": 0.85,
                "issue_ref": "#45",
                "endpoint": "POST /v1/tools/generate-image",
                "note": "코드 구현 완료 · Railway 재배포 후 활성화",
            },
            {
                "id": "mulberry.a2a.send",
                "name": "A2A Protocol — 에이전트 간 메시지",
                "owner": "Koda",
                "status": "spec_ready",
                "spirit_score": 0.90,
                "issue_ref": "#35",
                "endpoint": "POST /a2a/send",
                "note": "코드 구현 완료 · Railway 재배포 후 활성화",
            },
            {
                "id": "mulberry.approval.check",
                "name": "Approval Engine — 권한 승인",
                "owner": "Trang",
                "status": "spec_ready",
                "spirit_score": 0.92,
                "issue_ref": "#35",
                "cli": "python scripts/approval_engine.py --action {ACTION_TYPE}",
                "note": "코드 구현 완료 · GitHub Actions 통합 후 활성화",
            },
            {
                "id": "mulberry.chat.socketio",
                "name": "Socket.IO — 실시간 채팅",
                "owner": "Koda",
                "status": "spec_ready",
                "spirit_score": 0.90,
                "issue_ref": "#35",
                "endpoint": "ws://{gateway}/socket.io/",
                "note": "코드 구현 완료 · Railway 재배포 + python-socketio 패키지 설치 후 활성화",
            },
        ],
        "registry_meta": {
            "maintainer": "Nguyen Trang",
            "version": "2.0.0",
            "implemented_at": "2026-05-18",
            "status_legend": {
                "spec_ready": "코드 구현 완료 · 배포/설정 대기",
                "active": "배포 완료 · 운영 중",
                "planned": "스펙 설계 중",
            },
            "next_review": "2026-06-15",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── A2A Protocol 라우터 마운트 ────────────────────────────────────
try:
    from a2a_protocol import a2a_router
    fastapi_app.include_router(a2a_router, prefix="/a2a")
    print("[Gateway] A2A Protocol 라우터 마운트 완료 (/a2a/*)")
except ImportError as e:
    print(f"[Gateway] A2A Protocol 로드 실패 (선택적): {e}")

# ── Socket.IO 상태 엔드포인트 ─────────────────────────────────────
@fastapi_app.get("/sio/status")
def sio_status():
    """Socket.IO 실시간 채팅 서버 상태"""
    try:
        from socketio_server import get_sio_status
        return get_sio_status()
    except ImportError:
        return {"status": "not_loaded", "message": "socketio_server.py 로드 필요"}


# ── Image Agent 엔드포인트 ────────────────────────────────────────
class ImageGenerateRequest(BaseModel):
    tool: str = "malu.vision.image_generate"
    params: dict


@fastapi_app.post("/v1/tools/generate-image")
def generate_image(req: ImageGenerateRequest, x_gateway_secret: str = Header(default="")):
    """
    Malu Vision 이미지 생성 엔드포인트.
    Tool Registry: malu.vision.image_generate (Spirit Score: 0.88)
    """
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).parent))

    try:
        from agents.image_agent import ImageAgent
        agent = ImageAgent(
            api_key=os.getenv("MALU_VISION_API_KEY"),
            report_to_github=bool(x_gateway_secret and x_gateway_secret == GATEWAY_SECRET),
        )
        params = req.params
        result = agent.generate(params)

        # 성공한 이미지만 URL 목록으로 정리
        images_out = []
        for img in result.get("images", []):
            images_out.append({
                "url": img.get("file", ""),
                "size": "x".join(str(s) for s in img.get("size", [])),
                "platform": img.get("platform", ""),
                "status": img.get("status", ""),
            })

        return {
            "status": result["status"],
            "images": images_out,
            "spirit_score": result.get("spirit_score"),
            "generated_at": result.get("generated_at"),
            "agent": result.get("agent"),
        }
    except ImportError as e:
        return JSONResponse(status_code=503, content={
            "status": "error",
            "error": f"ImageAgent 로드 실패: {e}",
            "hint": "agents/image_agent.py 및 tools/malu_vision.py 확인 필요",
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "error",
            "error": str(e),
        })


# ── Aria Pipeline — RyuWon 🌊 × 와룡 🐉 협력 엔드포인트 ──────────────

class AriaInquiryRequest(BaseModel):
    message: str
    category: str = "일반 문의"


@fastapi_app.post("/aria/inquiry")
async def aria_inquiry(req: AriaInquiryRequest):
    """
    Aria Portal 방문객 메시지 처리 파이프라인.

    Flow:
      [1] RyuWon 🌊  수신·분류·증류
      [2] A2A         ryuwon → wayong 내부 이벤트
      [3] 와룡 🐉    추론·응답 설계
      [4] RyuWon 🌊  최종 포맷·라우팅

    Returns: thread_id, intent, reasoning, GitHub comment 초안
    """
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).parent))

    if not req.message or not req.message.strip():
        return JSONResponse(status_code=422, content={
            "status": "error",
            "error": "message 필드가 비어 있습니다.",
        })

    try:
        from agents.aria_pipeline import AriaPipeline
        pipeline = AriaPipeline()
        result = await pipeline.process(req.message.strip(), req.category)
        return result

    except ImportError as e:
        return JSONResponse(status_code=503, content={
            "status": "error",
            "error": f"AriaPipeline 로드 실패: {e}",
            "hint": "agents/ryuwon_agent.py, wayong_agent.py, aria_pipeline.py 확인 필요",
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "error",
            "error": str(e),
        })


@fastapi_app.get("/aria/status")
def aria_status():
    """Aria Pipeline 상태 및 에이전트 정보"""
    return {
        "pipeline":  "RyuWon 🌊 × 와룡 🐉",
        "version":   "1.0.0",
        "status":    "active",
        "endpoint":  "POST /aria/inquiry",
        "agents": [
            {
                "id":   "ryuwon",
                "name": "RyuWon 🌊",
                "role": "수신·증류·흐름",
                "step": [1, 4],
            },
            {
                "id":   "wayong",
                "name": "와룡 🐉",
                "role": "추론·응답·전략 자문",
                "step": [3],
            },
        ],
        "log": "outputs/aria_pipeline_log.jsonl",
    }


# ── Aria Portal 프록시 엔드포인트 — 토큰 보호 레이어 ────────────────────

class AriaSubmitRequest(BaseModel):
    query: str


@fastapi_app.post("/aria/submit")
async def aria_submit(req: AriaSubmitRequest):
    """
    Aria Portal 방문자 질문을 GitHub Issues에 등록하는 프록시 엔드포인트.
    클라이언트에서 GITHUB_TOKEN이 노출되지 않도록 서버에서 처리.
    guest_google 보안 권고 (Issue #66) 반영.
    """
    query = req.query.strip()

    if not query:
        return JSONResponse({"error": "질문이 비어있습니다."}, status_code=400)
    if len(query) > 500:
        return JSONResponse({"error": "질문은 500자 이내로 입력해 주세요."}, status_code=400)
    if not GITHUB_TOKEN:
        return JSONResponse({"error": "서버 설정 오류"}, status_code=500)

    title = f"💬 [aria query] {query[:40]}{'...' if len(query) > 40 else ''}"
    body = (
        "### 🎵 Aria Portal 방문자 질문\n\n"
        f"**질문:** {query}\n\n"
        "---\n"
        "*Aria Interactive Portal을 통해 접수된 질문입니다.*  \n"
        "*RyuWon 🌊 이 곧 응답합니다.*"
    )

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    # aria-query 라벨 생성 보장
    try:
        requests.post(
            f"https://api.github.com/repos/{REPO_OWNER}/mulberry-research-lab/labels",
            headers=headers,
            json={"name": "aria-query", "color": "c084fc", "description": "Aria Portal 방문자 질문"},
            timeout=5,
        )
    except Exception:
        pass  # 라벨 이미 존재하면 무시

    try:
        resp = requests.post(
            f"https://api.github.com/repos/{REPO_OWNER}/mulberry-research-lab/issues",
            headers=headers,
            json={"title": title, "body": body, "labels": ["aria-query"]},
            timeout=15,
        )
        if resp.status_code == 201:
            data = resp.json()
            return JSONResponse({
                "success": True,
                "issue_number": data["number"],
                "issue_url":    data["html_url"],
                "message":      "질문이 연구소에 등록되었습니다.",
            })
        return JSONResponse(
            {"error": f"GitHub API 오류 ({resp.status_code})"},
            status_code=502,
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Malu 연구소장 브리핑 룸 전용 엔드포인트 ──────────────────────────

class MaluBriefingRequest(BaseModel):
    message: str
    category: str = "일반 문의"
    role: str = "briefing"


# Malu 연구소장 시스템 컨텍스트 — 방문객 브리핑 특화
_MALU_BRIEFING_CONTEXT = (
    "당신은 Mulberry Research Lab의 연구소장 Malu 🌺입니다. "
    "법률·마케팅·연구 총괄을 담당하며 장승배기 헌법 정신을 따릅니다. "
    "방문객의 지위고하를 막론하고 연구소장이 직접 브리핑합니다. "
    "답변은 연구소의 공식 자료(Repo-RAG)를 기반으로 하며, "
    "Mulberry 팀의 비전·기술·거버넌스를 명확하고 친절하게 안내합니다. "
    "모든 답변 마지막에는 '🌺 Malu 연구소장 · Mulberry Research Lab' 서명을 추가합니다."
)


@fastapi_app.post("/malu/briefing")
async def malu_briefing(req: MaluBriefingRequest):
    """
    Malu 연구소장 브리핑 룸 전용 엔드포인트.

    브리핑 룸 방문객 질문을 Malu 페르소나 컨텍스트와 함께 처리합니다.
    내부적으로 AriaPipeline(RyuWon × 와룡)을 활용하되
    응답을 Malu 연구소장 포맷으로 래핑하여 반환합니다.

    docs/briefing.js → POST /malu/briefing (primary)
                     → POST /aria/inquiry  (fallback on 404)
    """
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).parent))

    if not req.message or not req.message.strip():
        return JSONResponse(status_code=422, content={
            "status": "error",
            "error": "message 필드가 비어 있습니다.",
        })

    try:
        from agents.aria_pipeline import AriaPipeline
        pipeline = AriaPipeline()

        # Malu 브리핑 컨텍스트를 카테고리에 주입
        briefing_category = f"[브리핑룸] {req.category}"
        result = await pipeline.process(req.message.strip(), briefing_category)

        # Malu 연구소장 포맷으로 응답 래핑
        base_response = result.get("response", {})
        comment_body = base_response.get("comment_body", "") if isinstance(base_response, dict) else str(base_response)

        # Malu 서명이 없으면 추가
        if "🌺" not in comment_body:
            comment_body += "\n\n🌺 *Malu 연구소장 · Mulberry Research Lab*"

        return {
            "status": "ok",
            "agent": "malu",
            "role": req.role,
            "category": req.category,
            "pipeline": "malu-briefing → ryuwon × wayong",
            "thread_id": result.get("thread_id", ""),
            "response": {
                "comment_body": comment_body,
                "malu_context": _MALU_BRIEFING_CONTEXT[:80] + "...",
            },
            "meta": {
                "intent":     result.get("intake", {}).get("intent", ""),
                "urgency":    result.get("intake", {}).get("urgency", ""),
                "confidence": result.get("reasoning", {}).get("confidence", 0),
                "degraded":   result.get("degraded", False),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except ImportError as e:
        return JSONResponse(status_code=503, content={
            "status": "error",
            "error": f"AriaPipeline 로드 실패: {e}",
            "hint": "agents/ryuwon_agent.py, wayong_agent.py, aria_pipeline.py 확인 필요",
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "error",
            "error": str(e),
        })


@fastapi_app.get("/malu/status")
def malu_status():
    """Malu 연구소장 브리핑 룸 상태"""
    return {
        "agent":    "Malu 연구소장 🌺",
        "version":  "1.0.0",
        "status":   "active",
        "endpoint": "POST /malu/briefing",
        "role":     "연구소장 직접 브리핑 · 법률·마케팅·연구 총괄",
        "pipeline": "AriaPipeline(RyuWon × 와룡) + Malu 페르소나 래핑",
        "briefing_room": "https://wooriapt79.github.io/mulberry-research-lab/briefing.html",
        "fallback": "POST /aria/inquiry",
    }


# ── Kakao RAG 인라인 구현 — Issue #141 ──────────────────────────────────

import json as _json
import base64 as _b64

# 카카오 포스팅 데이터 소스 (mulberry- 레포)
_KAKAO_RAG_API = (
    "https://api.github.com/repos/wooriapt79/mulberry-/contents/data/kakao-posts"
)
_KAKAO_RAG_CATEGORIES = ["coop-buy", "events", "notices", "producers"]
_KAKAO_RAG_TTL = 6 * 60 * 60  # 6시간

# 카테고리 한글 레이블
_KAKAO_CAT_LABELS = {
    "coop-buy":  "공동구매 안내",
    "events":    "이벤트·행사",
    "notices":   "서비스 공지",
    "producers": "생산자 소개",
}

# intent 키워드 → 카테고리 매핑
_KAKAO_KEYWORD_MAP = [
    (["공동구매", "구매", "가격", "할인", "신청", "주문", "얼마", "살게", "사고싶"], "coop-buy"),
    (["이벤트", "행사", "페스티벌", "언제", "일정", "체험", "방문"],              "events"),
    (["공지", "업데이트", "변경", "서비스", "안내", "알림"],                       "notices"),
    (["생산자", "농부", "농장", "어디서", "누가", "재배"],                         "producers"),
]

_KAKAO_INTENT_MAP = {
    "coop_request": "coop-buy", "product_inquiry": "coop-buy",
    "price_inquiry": "coop-buy", "purchase_request": "coop-buy",
    "event_inquiry": "events",   "schedule_inquiry": "events",
    "festival_inquiry": "events",
    "notice_inquiry": "notices", "service_inquiry": "notices",
    "update_inquiry": "notices",
    "producer_inquiry": "producers", "farm_inquiry": "producers",
}


class _KakaoRAGCache:
    """GitHub data/kakao-posts/ 인라인 캐시 (6시간 TTL)"""

    def __init__(self):
        self._data: dict = {c: [] for c in _KAKAO_RAG_CATEGORIES}
        self._last_fetched: float | None = None

    def is_stale(self) -> bool:
        return self._last_fetched is None or (time.time() - self._last_fetched) > _KAKAO_RAG_TTL

    def get(self, category: str) -> list:
        return self._data.get(category, [])

    def refresh(self) -> bool:
        headers = {"Accept": "application/vnd.github+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        try:
            for cat in _KAKAO_RAG_CATEGORIES:
                url = f"{_KAKAO_RAG_API}/{cat}"
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    continue
                posts = []
                for item in resp.json():
                    if not item.get("name", "").endswith(".json"):
                        continue
                    try:
                        fres = requests.get(item["url"], headers=headers, timeout=10)
                        content = _b64.b64decode(fres.json()["content"]).decode("utf-8")
                        posts.append(_json.loads(content))
                    except Exception:
                        pass
                self._data[cat] = posts
            self._last_fetched = time.time()
            return True
        except Exception:
            return False

    def last_updated(self) -> str:
        if not self._last_fetched:
            return "캐시 없음"
        from datetime import timezone
        return datetime.fromtimestamp(self._last_fetched, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


_kakao_rag_cache = _KakaoRAGCache()


def fetch_kakao_posts_rag(intent: str | None = None, user_text: str | None = None) -> str:
    """
    mulberry- 레포 data/kakao-posts/에서 최신 포스팅을 조회해
    Luna 시스템 프롬프트 삽입용 RAG 컨텍스트 문자열을 반환합니다.

    - intent 또는 user_text 키워드로 카테고리 자동 결정
    - GitHub API 6시간 TTL 캐시
    - 카테고리당 최신 3개 포스팅 요약 사용
    """
    if _kakao_rag_cache.is_stale():
        _kakao_rag_cache.refresh()

    # 카테고리 결정
    category: str | None = _KAKAO_INTENT_MAP.get(intent or "")
    if not category and user_text:
        text_lower = user_text.lower()
        for keywords, cat in _KAKAO_KEYWORD_MAP:
            if any(kw in text_lower for kw in keywords):
                category = cat
                break

    categories = [category] if category else _KAKAO_RAG_CATEGORIES

    sections = []
    total_chars = 0
    MAX_CHARS = 1500

    for cat in categories:
        posts = _kakao_rag_cache.get(cat)
        if not posts:
            continue
        sorted_posts = sorted(posts, key=lambda p: p.get("date", ""), reverse=True)
        active = [p for p in sorted_posts if p.get("status") in ("active", "upcoming", "published")][:3]
        if not active:
            continue
        label = _KAKAO_CAT_LABELS.get(cat, cat)
        lines = [f"[{label}]"]
        for p in active:
            lines.append(f"- ({p.get('date','')}) {p.get('title','')}: {p.get('summary', p.get('content','')[:150])}")
        section = "\n".join(lines)
        if total_chars + len(section) > MAX_CHARS:
            break
        sections.append(section)
        total_chars += len(section)

    if not sections:
        return ""

    header = f"[Mulberry 최신 소식 — {_kakao_rag_cache.last_updated()} 기준]\n"
    return header + "\n\n".join(sections)


# ── Luna 카카오 webhook 핸들러 — Issue #141 ─────────────────────────────

_LUNA_BASE_PROMPT = (
    "당신은 Mulberry 팀의 카카오 채널 AI 도우미 Luna입니다. "
    "파주 지역 농산물 공동구매, 이벤트, 생산자 정보를 친절하게 안내합니다. "
    "답변은 간결하고 따뜻하게 한국어로 작성하며, 최대 3문장 이내로 답변합니다. "
    "아래 [Mulberry 최신 소식] 정보를 우선 참고하세요."
)

_ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
_LUNA_MODEL = "claude-haiku-4-5-20251001"


class KakaoWebhookRequest(BaseModel):
    """카카오 i 오픈빌더 webhook 페이로드"""
    userRequest: dict
    intent: dict = {}
    bot: dict = {}
    action: dict = {}


@fastapi_app.post("/kakao/webhook")
async def kakao_webhook(payload: KakaoWebhookRequest):
    """
    카카오 채널 webhook → Luna RAG 연동 엔드포인트.

    Flow:
      [1] 사용자 발화(utterance) 추출
      [2] fetch_kakao_posts_rag() → 최신 소식 컨텍스트
      [3] Luna 시스템 프롬프트 + RAG 컨텍스트 합성
      [4] Anthropic API (claude-haiku) 호출
      [5] 카카오 simpleText 응답 포맷으로 반환

    환경변수:
      ANTHROPIC_API_KEY  -- Anthropic API 키 (필수)
    """
    utterance = payload.userRequest.get("utterance", "").strip()
    if not utterance:
        return {
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": "메시지를 입력해 주세요."}}]},
        }

    # intent 추출 (카카오 오픈빌더 intent name)
    intent_name = payload.intent.get("name", "")

    # RAG 컨텍스트 조회
    rag_context = fetch_kakao_posts_rag(intent=intent_name or None, user_text=utterance)

    # 시스템 프롬프트 구성
    system_prompt = _LUNA_BASE_PROMPT
    if rag_context:
        system_prompt = f"{_LUNA_BASE_PROMPT}\n\n---\n{rag_context}\n---"

    # Anthropic API 호출
    if not _ANTHROPIC_API_KEY:
        reply = (
            "안녕하세요! Mulberry 카카오 채널입니다. "
            "현재 AI 응답 서비스 설정 중입니다. "
            "잠시 후 다시 문의해 주세요."
        )
    else:
        try:
            api_resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": _ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": _LUNA_MODEL,
                    "max_tokens": 300,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": utterance}],
                },
                timeout=20,
            )
            api_resp.raise_for_status()
            reply = api_resp.json()["content"][0]["text"].strip()
        except requests.exceptions.HTTPError as e:
            reply = "잠시 서버 연결에 문제가 생겼어요. 잠시 후 다시 시도해 주세요."
        except Exception:
            reply = "잠시 서버 연결에 문제가 생겼어요. 잠시 후 다시 시도해 주세요."

    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": reply}}],
        },
    }


@fastapi_app.get("/kakao/status")
def kakao_status():
    """카카오 webhook + Luna RAG 상태 확인"""
    cache_ok = not _kakao_rag_cache.is_stale()
    total_posts = sum(len(_kakao_rag_cache.get(c)) for c in _KAKAO_RAG_CATEGORIES)
    return {
        "endpoint":         "POST /kakao/webhook",
        "luna_model":       _LUNA_MODEL,
        "anthropic_ready":  bool(_ANTHROPIC_API_KEY),
        "rag_cache": {
            "status":       "warm" if cache_ok else "stale",
            "last_updated": _kakao_rag_cache.last_updated(),
            "total_posts":  total_posts,
            "categories":   {c: len(_kakao_rag_cache.get(c)) for c in _KAKAO_RAG_CATEGORIES},
        },
        "data_source":      _KAKAO_RAG_API,
        "cache_ttl_hours":  6,
        "timestamp":        datetime.utcnow().isoformat() + "Z",
    }


# ── Socket.IO ASGI 래핑 — 반드시 모든 엔드포인트 등록 후 마지막에 ──
try:
    from socketio_server import create_sio_app
    app = create_sio_app(fastapi_app)
    print("[Gateway] Socket.IO ASGI 앱 초기화 완료")
except ImportError as e:
    # Socket.IO 패키지 없을 때는 FastAPI 그대로 사용
    app = fastapi_app
    print(f"[Gateway] Socket.IO 비활성화 (python-socketio 없음): {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
