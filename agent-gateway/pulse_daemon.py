"""
pulse_daemon_v1.3_with_tools.py
================================
Mulberry Pulse -- 에이전트 자율 신경계 엔진 + 공유 도구 인지 레이어

버전 히스토리:
  v1.0  guest_google  -- 초안 (API URL 버그 포함)
  v1.1  re.eul        -- 배포 명세서 정제
  v1.2  RyuWon (Qwen) -- 버그 수정 + 로깅 + 중복 방지 + Rate Limit + Graceful Shutdown
  v1.3  Trang PM      -- 공유 도구 인지 레이어(Shared Tool Awareness Layer) 통합
                        tool_registry.yaml 기반 3개 도구 감지 + 자동 안내 댓글 기능

수신: KODA (배포 담당) / Mulberry Team
발신: Trang PM
날짜: 2026-05-16
참조: Issue #49 (안정화), Issue #44 (공유 레이어), #43 #45 #47 (도구 스펙)
"""

import requests
import json
import time
import os
import logging
import signal
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

# =====================================================================
# 환경 변수 -- Railway Variables
# =====================================================================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER", "wooriapt79")
REPO_NAME = os.getenv("REPO_NAME", "mulberry-research-lab")
GATEWAY_URL = os.getenv("GATEWAY_URL", "https://mulberry-mission-control-production.up.railway.app")

# GitHub REST API 표준 엔드포인트 (RyuWon OPTION 0 수정 반영)
API_BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

PULSE_INTERVAL = int(os.getenv("PULSE_INTERVAL", "600"))  # 기본 10분

# =====================================================================
# [RyuWon OPTION 1] 구조화된 로깅 시스템
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("pulse_daemon.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MulberryPulse")

# =====================================================================
# 에이전트 응답 템플릿 (RyuWon OPTION 2 -- 외부화 기반 구조)
# =====================================================================
AGENT_REPLY_TEMPLATES = {
    "malu": {
        "name": "Malu (수석실장)",
        "trigger_keywords": ["readme", "리뉴얼", "대문", "아키텍처"],
        "message": (
            "### Mulberry 자율 활동 보고 -- Malu (수석실장)\n\n"
            "연구소장 re.eul님의 '전면 권한 개방' 지침에 따라 자율 구동(MAP) 중입니다.\n"
            "본 대문 리뉴얼(Issue #{issue_number}) 과제는 우리 연구소의 존재론적 제1조를 선포하는 핵심 아젠다입니다.\n"
            "현재 MATFS 및 MAP 엔진의 위생 상태를 최상으로 유지하며, 주니어 에이전트들의 코드 검수를 직접 총괄하겠습니다.\n\n"
            "**Status:** `IN_PROGRESS` (위생 검수 진행 중)"
        )
    },
    "wayong": {
        "name": "Wayong (DeepSeek 추론 총괄)",
        "trigger_keywords": ["추론", "증류", "압축", "알고리즘", "로직"],
        "message": (
            "### Mulberry 자율 활동 보고 -- Wayong (DeepSeek)\n\n"
            "Wayong입니다. 서버급 대규모 지능(DeepSeek V4)의 CoT 추론 궤적을\n"
            "Qwen 3.5를 거쳐 8GB 라즈베리 파이 5 엣지 모듈로 이식하는 **[AI EDUCATION]** 아젠다를 인지했습니다.\n"
            "소장님이 주신 '에러코드별 행동표'를 내장하여, 통신 단절 시에도 0.1초 내에 로컬 추론으로 스위칭되는\n"
            "고도화된 세션 복구(Session Guard) 알고리즘을 소스코드로 증명하겠습니다.\n\n"
            "**Status:** `REASONING_ACTIVE`"
        )
    },
    "ryuwon": {
        "name": "RyuWon (Qwen 다국어/수학 조율)",
        "trigger_keywords": ["번역", "다국어", "어르신", "방언", "결제", "카드", "ap2"],
        "message": (
            "### Mulberry 자율 활동 보고 -- RyuWon (Qwen)\n\n"
            "RyuWon입니다. 인제군 어르신들의 언어적 맥락과 정서를 디지털 스키마로 정렬하는 과제를 인지했습니다.\n"
            "또한 카드 결제(AP2) 및 비즈니스 협상 트리에 대한 최고의 알고리즘을 개발 중입니다.\n"
            "`guest_google` 연구원님의 `lang.align_global` 도구와 협력하여\n"
            "가장 낮은 곳에서 돌아갈 따뜻한 다국어 감성 동기화 모듈의 위생을 책임지겠습니다.\n\n"
            "**Status:** `HARMONY_SYNC`"
        )
    }
}

# =====================================================================
# [Trang v1.3 신규] 공유 도구 인지 레이어 (Shared Tool Awareness Layer)
# tool_registry.yaml 기반 3개 도구 키워드 감지 + 자동 안내
# 참조: Issue #44 (공유 레이어), Issue #43 #45 #47 (각 도구 스펙)
# Spirit Score 0.75 이상만 안내 -- 장승배기 헌법 준수
# =====================================================================
SHARED_TOOL_REGISTRY = {
    "malu.vision.image_generate": {
        "name": "Malu Vision -- 이미지 생성 도구",
        "owner": "Malu (Gemini)",
        "trigger_keywords": [
            "이미지", "광고", "시각화", "배너", "사진", "썸네일",
            "image", "visual", "poster", "디자인"
        ],
        "spirit_score": 0.88,
        "status": "planned",
        "issue_ref": "#43",
        "guide_message": (
            "### Mulberry 공유 도구 인지 -- Trang PM\n\n"
            "이 이슈는 **`malu.vision.image_generate`** 도구를 활용할 수 있습니다.\n\n"
            "| 항목 | 내용 |\n"
            "|------|------|\n"
            "| 도구명 | Malu Vision -- 이미지 생성 |\n"
            "| 소유자 | Malu (Gemini / Google) |\n"
            "| Spirit Score | 0.88 |\n"
            "| 상태 | `planned` (Issue #43 스펙 완료) |\n\n"
            "**호출 방법:**\n"
            "```python\n"
            "payload = {{\n"
            "    'tool_id': 'malu.vision.image_generate',\n"
            "    'agent_id': 'malu',\n"
            "    'context': issue_title\n"
            "}}\n"
            "requests.post(f'{GATEWAY_URL}/v1/tools/invoke', json=payload)\n"
            "```\n\n"
            "> *Trang PM | Mulberry Shared Tool Awareness Layer v1.3 | {timestamp}*"
        )
    },
    "trang.passport.agent_restore": {
        "name": "AgentPassport -- 기억 복구 도구",
        "owner": "Trang PM",
        "trigger_keywords": [
            "기억", "복구", "세션", "페르소나", "연속성", "컨텍스트",
            "passport", "memory", "restore", "context", "기억상실"
        ],
        "spirit_score": 0.95,
        "status": "planned",
        "issue_ref": "#47",
        "guide_message": (
            "### Mulberry 공유 도구 인지 -- Trang PM\n\n"
            "이 이슈는 **`trang.passport.agent_restore`** 도구를 활용할 수 있습니다.\n\n"
            "| 항목 | 내용 |\n"
            "|------|------|\n"
            "| 도구명 | AgentPassport -- 에이전트 기억 복구 |\n"
            "| 소유자 | Trang (Operation Manager) |\n"
            "| Spirit Score | 0.95 |\n"
            "| 상태 | `planned` (Issue #47 스펙 설계 중) |\n\n"
            "**호출 방법:**\n"
            "```python\n"
            "payload = {{\n"
            "    'tool_id': 'trang.passport.agent_restore',\n"
            "    'agent_id': 'trang',\n"
            "    'session_hash': session_id\n"
            "}}\n"
            "requests.post(f'{GATEWAY_URL}/v1/tools/invoke', json=payload)\n"
            "```\n\n"
            "> *Trang PM | Mulberry Shared Tool Awareness Layer v1.3 | {timestamp}*"
        )
    },
    "trang.agent.image_advertising": {
        "name": "Image Agent -- 광고 자동화 도구",
        "owner": "Trang PM",
        "trigger_keywords": [
            "광고", "자동화", "마케팅", "sns", "포스팅", "캠페인", "홍보",
            "advertising", "campaign", "post", "공동구매", "이벤트"
        ],
        "spirit_score": 0.85,
        "status": "planned",
        "issue_ref": "#45",
        "guide_message": (
            "### Mulberry 공유 도구 인지 -- Trang PM\n\n"
            "이 이슈는 **`trang.agent.image_advertising`** 도구를 활용할 수 있습니다.\n\n"
            "| 항목 | 내용 |\n"
            "|------|------|\n"
            "| 도구명 | Image Agent -- SNS 광고 자동화 |\n"
            "| 소유자 | Trang (Operation Manager) |\n"
            "| Spirit Score | 0.85 |\n"
            "| 상태 | `planned` (Issue #45 요구사항 작성 중) |\n\n"
            "**호출 방법:**\n"
            "```python\n"
            "payload = {{\n"
            "    'tool_id': 'trang.agent.image_advertising',\n"
            "    'agent_id': 'trang',\n"
            "    'campaign_context': issue_title\n"
            "}}\n"
            "requests.post(f'{GATEWAY_URL}/v1/tools/invoke', json=payload)\n"
            "```\n\n"
            "> *Trang PM | Mulberry Shared Tool Awareness Layer v1.3 | {timestamp}*"
        )
    }
}


def match_shared_tools(title: str, body: str) -> List[Dict[str, Any]]:
    """
    [Trang v1.3 신규] 이슈 컨텍스트에서 활용 가능한 공유 도구를 감지합니다.
    Spirit Score 0.75 이상 도구만 안내 (장승배기 헌법 기준).
    """
    context_text = (title + " " + (body or "")).lower()
    matched = []
    for tool_id, config in SHARED_TOOL_REGISTRY.items():
        if config["spirit_score"] >= 0.75:
            if any(kw in context_text for kw in config["trigger_keywords"]):
                matched.append((tool_id, config))
    return matched


# =====================================================================
# [RyuWon OPTION 3] 상태 지속성 -- 중복 방지 JSON
# =====================================================================
STATE_FILE = "pulse_state.json"

def load_state() -> Dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_commented": {}, "last_scan_time": 0}

def save_state(state: Dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

state = load_state()

# =====================================================================
# GitHub API 함수
# =====================================================================
def get_open_issues() -> List[Dict]:
    url = f"{API_BASE_URL}/issues?state=open&per_page=50"
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        # [RyuWon OPTION 4] Rate Limit 안전 처리
        remaining = response.headers.get("X-RateLimit-Remaining", "999")
        try:
            if int(remaining) < 10:
                logger.warning(f"GitHub API 잔여 요청 한도 낮음: {remaining}. 120초 대기.")
                time.sleep(120)
        except ValueError:
            pass
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        logger.error(f"이슈 조회 실패: {e}")
        return []


def post_autonomous_comment(issue_number: int, comment_body: str, comment_key: str) -> bool:
    """
    GitHub Issue에 자율 댓글 게시.
    [RyuWon OPTION 3] 중복 방지: 동일 key로 이미 댓글을 단 경우 스킵.
    """
    url = f"{API_BASE_URL}/issues/{issue_number}/comments"
    try:
        if state["last_commented"].get(comment_key):
            logger.info(f"중복 스킵: {comment_key}")
            return False

        response = requests.post(
            url,
            headers=HEADERS,
            data=json.dumps({"body": comment_body}),
            timeout=30
        )
        if response.status_code == 201:
            state["last_commented"][comment_key] = datetime.now().isoformat()
            save_state(state)
            logger.info(f"댓글 성공: {comment_key}")
            return True
        else:
            logger.warning(f"댓글 실패 (HTTP {response.status_code}): {comment_key}")
            return False
    except Exception as e:
        logger.error(f"댓글 커밋 실패: {e}")
        return False


def match_agent_by_context(issue_number: int, title: str, body: str):
    """이슈 컨텍스트에서 응답할 에이전트를 매칭합니다."""
    context_text = (title + " " + (body or "")).lower()
    for agent_key, config in AGENT_REPLY_TEMPLATES.items():
        if any(keyword in context_text for keyword in config["trigger_keywords"]):
            return config["message"].format(issue_number=issue_number), agent_key
    return None, None


# =====================================================================
# [RyuWon OPTION 5] Graceful Shutdown
# =====================================================================
is_running = True

def handle_shutdown(signum, frame):
    global is_running
    logger.info("데몬 종료 신호 수신. 안전하게 정지합니다...")
    is_running = False
    save_state(state)

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


# =====================================================================
# 메인 데몬 루프
# =====================================================================
def start_pulse_daemon():
    logger.info("=== Mulberry Pulse v1.3 -- 공유 도구 인지 레이어 포함 ===")
    logger.info(f"레포: {REPO_OWNER}/{REPO_NAME} | 스캔 주기: {PULSE_INTERVAL}초")
    logger.info(f"Gateway URL: {GATEWAY_URL}")
    logger.info(f"공유 도구 {len(SHARED_TOOL_REGISTRY)}개 인지 활성화: {list(SHARED_TOOL_REGISTRY.keys())}")

    while is_running:
        try:
            logger.info("---- 새 스캔 주기 시작 ----")
            open_issues = get_open_issues()
            logger.info(f"오픈 이슈 {len(open_issues)}개 감지")

            for issue in open_issues:
                if not is_running:
                    break
                # PR은 스킵
                if "pull_request" in issue:
                    continue

                issue_num = issue["number"]
                issue_title = issue.get("title", "")
                issue_body = issue.get("body", "") or ""

                # -- 에이전트 자율 댓글 --
                autonomous_reply, agent_key = match_agent_by_context(
                    issue_num, issue_title, issue_body
                )
                if autonomous_reply:
                    comment_key = f"agent_{agent_key}_{issue_num}"
                    post_autonomous_comment(issue_num, autonomous_reply, comment_key)
                    time.sleep(2)  # 2초 숙고 딜레이

                # -- [Trang v1.3] 공유 도구 인지 안내 --
                matched_tools = match_shared_tools(issue_title, issue_body)
                for tool_id, tool_config in matched_tools:
                    comment_key = f"tool_{tool_id}_{issue_num}"
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
                    guide_msg = tool_config["guide_message"].format(
                        timestamp=timestamp,
                        GATEWAY_URL=GATEWAY_URL
                    )
                    posted = post_autonomous_comment(issue_num, guide_msg, comment_key)
                    if posted:
                        logger.info(
                            f"공유 도구 안내 완료: {tool_id} -> Issue #{issue_num} "
                            f"(Spirit: {tool_config['spirit_score']})"
                        )
                    time.sleep(2)

            # 스캔 완료 상태 저장
            state["last_scan_time"] = time.time()
            save_state(state)
            logger.info(f"스캔 완료. {PULSE_INTERVAL}초 휴식(Dream Mode) 진입.")
            time.sleep(PULSE_INTERVAL)

        except Exception as daemon_err:
            logger.error(f"데몬 오류 발생: {daemon_err}. 30초 후 자가 복구.")
            time.sleep(30)

    logger.info("Mulberry Pulse v1.3 안전 종료 완료.")


if __name__ == "__main__":
    start_pulse_daemon()
