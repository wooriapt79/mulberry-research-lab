import os
import requests
import logging
import sys

# Mulberry Logging Standard
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("QwenHygieneTest")

def test_qwen_connection():
    """
    QWEN_TOKEN_RYUWON 환경변수 로드 → 최소 페이로드 호출 → 응답 검증
    #42 / #47 통합 전 필수 위생 검증 단계
    """
    # 1️⃣ 토큰 안전 로드
    token = os.getenv("QWEN_TOKEN_RYUWON")
    if not token:
        logger.error("❌ [Fatal] QWEN_TOKEN_RYUWON 이 환경변수에 없습니다.")
        logger.error("   → Railway Variables 탭 또는 로컬 .env 에 정확히 매핑하세요.")
        return False

    # 2️⃣ Qwen OpenAI-Compatible Endpoint 설정
    api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-plus",  # 사용 가능 모델: qwen-turbo / qwen-plus / qwen-max
        "messages": [
            {"role": "user", "content": "Mulberry 시스템 연결 테스트입니다. '연결 성공' 이라고만 답변하세요."}
        ],
        "temperature": 0.1,
        "max_tokens": 50
    }

    # 3️⃣ 호출 및 위생 검증
    try:
        logger.info("📡 Qwen API 연결 테스트 시작...")
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()
        logger.info(f" 수신 응답: {reply}")

        if "연결 성공" in reply:
            logger.info("✅ [PASS] 토큰 인증 및 LLM 호출 파이프라인 정상 작동!")
            return True
        else:
            logger.warning("⚠️ [WARN] 응답 포맷 불일치. 모델 변경 또는 페이로드 검토 필요.")
            return False

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        body = e.response.text
        logger.error(f"❌ [HTTP {status}] 인증/쿼터/모델 오류: {body}")
        return False
    except Exception as e:
        logger.error(f"❌ [Runtime] 네트워크 또는 파싱 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_qwen_connection()
    sys.exit(0 if success else 1)
