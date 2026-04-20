# -*- coding: utf-8 -*-
"""
Mulberry Image Agent with Question Mode
- 이미지에서 텍스트 추출 (OCR)
- 규칙 기반 명령어 생성
- 불확실 시 사용자 질문 모드
- (TODO) 다음 연구: LLM 해석, 메타데이터 저장, 실제 Agent API 연동
"""

import json
import re
import requests
from PIL import Image
import pytesseract
from typing import Dict, Any, Optional

# ===============================
# 0. 의존성 설치 (Colab 전용)
# ===============================
# TODO: 다음 연구 - 로컬 환경에서도 자동 설치 스크립트 추가
def install_if_missing(package: str):
    try:
        __import__(package)
    except ImportError:
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_if_missing("pillow")
install_if_missing("requests")
install_if_missing("pytesseract")

# Tesseract OCR 엔진 설치 (Linux/Colab)
import os
if os.name == 'posix' and not os.path.exists('/usr/bin/tesseract'):
    import subprocess
    subprocess.check_call(['apt-get', 'update', '-qq'])
    subprocess.check_call(['apt-get', 'install', '-y', 'tesseract-ocr'])

# ===============================
# 1. 이미지 텍스트 추출
# ===============================
def extract_text_from_image(image_path: str) -> str:
    """
    이미지 파일에서 텍스트 추출 (OCR)
    TODO: 이미지 전처리(이진화, 노이즈 제거) 추가하여 정확도 향상
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        print(f"⚠️ OCR 오류: {e}")
        return ""

# ===============================
# 2. 텍스트 → 기본 명령어 매핑 (규칙 기반)
# ===============================
def text_to_agent_command(text: str) -> Dict[str, Any]:
    """
    추출된 텍스트에서 키워드를 찾아 Mulberry 명령어 생성.
    TODO: LLM 기반 해석기로 대체하거나 규칙 테이블 확장
    """
    text_lower = text.lower()
    command = {
        "agent_id": "assistant",
        "action": "chat",
        "params": {},
        "persona": None,
        "skills": []
    }
    
    # 한글 + 영문 키워드 매핑 (확장 가능)
    keyword_map = {
        "분석": {"action": "analyze", "agent": "lynn"},
        "데이터": {"skills": ["data_analysis"]},
        "처리": {"action": "process"},
        "모니터": {"action": "monitor"},
        "인사이트": {"action": "insight"},
        "보고": {"action": "report"},
        "협업": {"persona": "collaborative"},
        "친구": {"persona": "friendly"},
        "전략": {"agent": "waryong", "action": "strategy"},
        "주문": {"agent": "koda", "action": "order"},
        "물류": {"agent": "logistics", "action": "track"},
        "analyze": {"action": "analyze", "agent": "lynn"},
        "process": {"action": "process"},
        "monitor": {"action": "monitor"},
        "insight": {"action": "insight"},
        "report": {"action": "report"},
        "collab": {"persona": "collaborative"},
        "friend": {"persona": "friendly"},
        "strategy": {"agent": "waryong", "action": "strategy"},
        "order": {"agent": "koda", "action": "order"},
        "track": {"agent": "logistics", "action": "track"},
        "data": {"skills": ["data_analysis"]},
    }
    
    for keyword, mapping in keyword_map.items():
        if keyword in text_lower:
            for k, v in mapping.items():
                if k == "agent":
                    command["agent_id"] = v
                elif k == "action":
                    command["action"] = v
                elif k == "skills":
                    command["skills"].extend(v)
                elif k == "persona":
                    command["persona"] = v
                else:
                    command["params"][k] = v
    
    # 명령형 어미 감지 (예: "해줘")
    if re.search(r"(해줘|알려줘|줘)$", text_lower):
        command["action"] = command["action"] or "execute"
    
    return command

# ===============================
# 3. 사용자 질문 모드
# ===============================
def ask_user_for_command(extracted_text: str) -> Optional[Dict[str, Any]]:
    """
    명확한 명령어가 없을 때 사용자에게 옵션을 제시하고 입력을 받음.
    TODO: 사용자 피드백을 로그로 저장하여 학습 데이터로 활용
    """
    print("\n🤔 이미지에서 명확한 명령어를 찾지 못했습니다.")
    print(f"추출된 텍스트 미리보기: {extracted_text[:200]}")
    print("\n이 이미지로 무엇을 하시겠습니까?")
    print("1. 직접 명령어 입력 (예: 'analyze data', 'lynn에게 분석 요청')")
    print("2. 기본 에이전트 실행 (채팅 모드)")
    print("3. 다시 시도 (다른 이미지)")
    choice = input("선택 (1/2/3): ").strip()
    
    if choice == "1":
        user_input = input("명령어를 입력하세요: ")
        return text_to_agent_command(user_input)
    elif choice == "2":
        return {"agent_id": "assistant", "action": "chat", "params": {}, "persona": None, "skills": []}
    else:
        return None

# ===============================
# 4. Mulberry Agent 호출 (시뮬레이션)
# ===============================
def call_mulberry_agent(command: Dict[str, Any], api_endpoint: str = None) -> Dict[str, Any]:
    """
    생성된 명령어를 실제 Mulberry Agent API로 전송 (또는 시뮬레이션).
    TODO: 실제 AgentFactory REST API 연동 구현
    """
    if api_endpoint:
        try:
            response = requests.post(api_endpoint, json=command, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "command": command}
    else:
        print("\n🎭 [시뮬레이션] Mulberry Agent 호출:")
        print(json.dumps(command, indent=2, ensure_ascii=False))
        return {
            "status": "simulated",
            "message": f"에이전트 '{command['agent_id']}'가 '{command['action']}' 작업을 실행했습니다.",
            "command": command
        }

# ===============================
# 5. 메인 파이프라인
# ===============================
def run_image_agent(image_path: str, api_endpoint: str = None):
    """
    전체 실행 흐름: 이미지 → 텍스트 → 명령어 → (질문) → 에이전트 호출
    """
    print(f"🖼️ 이미지 분석 중: {image_path}")
    text = extract_text_from_image(image_path)
    if not text:
        print("⚠️ 이미지에서 텍스트를 추출하지 못했습니다.")
        return
    
    print(f"📝 추출된 텍스트:\n{text[:500]}\n")
    command = text_to_agent_command(text)
    
    # 기본 명령어(assistant/chat)이면서 추가 파라미터 없으면 질문 모드
    if command["agent_id"] == "assistant" and command["action"] == "chat" and not command["params"]:
        user_cmd = ask_user_for_command(text)
        if user_cmd is None:
            print("⏩ 작업을 취소하고 다시 시도합니다.")
            return
        command = user_cmd
    
    print(f"🎯 최종 명령어:\n{json.dumps(command, indent=2, ensure_ascii=False)}\n")
    result = call_mulberry_agent(command, api_endpoint)
    print(f"✅ 실행 결과:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
    return result

# ===============================
# 실행 (Colab 환경)
# ===============================
if __name__ == "__main__":
    # 자동으로 업로드된 첫 번째 이미지 선택
    import glob
    image_files = glob.glob("*.png") + glob.glob("*.jpg") + glob.glob("*.jpeg")
    if not image_files:
        print("⚠️ 이미지 파일이 없습니다. 먼저 업로드해 주세요.")
        from google.colab import files
        uploaded = files.upload()
        image_files = list(uploaded.keys())
    image_path = image_files[0]
    print(f"✅ 분석할 이미지: {image_path}")
    
    # 실제 API 엔드포인트가 없으면 None (시뮬레이션)
    MULBERRY_API = None  # TODO: 추후 실제 API 주소로 변경
    
    run_image_agent(image_path, MULBERRY_API)
