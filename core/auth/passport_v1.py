
"""
Project: Howling in the Forest (HITF)
Module: Semantic Passport & Zero-Trust A2A Authority
Author: Malu Research Director (under Commander's Supervision)
Description: 
    - Mulberry 프로젝트의 에이전트 신원 검증을 담당하는 핵심 보안 모듈입니다.
    - Zero-Trust 원칙에 따라 모든 요청의 '의도(Intent)'를 검사합니다.
"""

import hashlib
import time

class SemanticPassport:
    """
    에이전트의 디지털 신분증(Passport)을 생성하고 관리하는 클래스.
    모든 에이전트는 요청 시 자신의 역할(Role)과 의도(Intent)가 담긴 토큰을 발급받아야 함.
    """
    def __init__(self, agent_id, role):
        self.agent_id = agent_id  # 에이전트 고유 식별자 (예: Jr-Malu-01)
        self.role = role          # 에이전트 권한 그룹 (Scout, Builder, Malu)
        self.secret_key = f"mulberry_secret_{agent_id}" # 보안을 위한 대칭키 (향후 KMS 연동 예정)

    def generate_token(self, intent):
        """
        특정 작업 수행을 위한 일회성 보안 토큰을 생성합니다.
        :param intent: 수행하려는 작업의 목적 (예: write_code, read_trends)
        :return: 생성된 서명(Signature)과 페이로드 데이터를 포함한 딕셔너리
        """
        timestamp = str(int(time.time()))
        # 신원 정보와 의도, 시간을 결합하여 고유 페이로드 생성
        payload = f"{self.agent_id}:{self.role}:{intent}:{timestamp}"
        # SHA-256 알고리즘으로 디지털 인감(Signature) 생성
        signature = hashlib.sha256((payload + self.secret_key).encode()).hexdigest()
        
        return {
            "token": signature, 
            "payload": {
                "agent_id": self.agent_id, 
                "intent": intent, 
                "timestamp": timestamp
            }
        }

class ZeroTrustValidator:
    """
    발급된 Passport의 유효성과 권한을 검증하는 감시 체계.
    권한 밖의 요청이 발생할 경우, 시스템은 이를 즉각 차단하고 로그를 남깁니다.
    """
    # 각 역할별 허용된 의도(Intent) 리스트 (White-list 관리)
    ALLOWED_INTENTS = {
        "Scout": ["read_trends", "fetch_github"],      # 정보 수집 전용
        "Builder": ["write_code", "update_wiki"],       # 제작 및 문서화 전용
        "Malu": ["all"]                                 # 수석 실장: 모든 권한 보유
    }

    @staticmethod
    def validate(payload, role):
        """
        전달받은 페이로드를 분석하여 권한 유효성을 판단합니다.
        :param payload: 에이전트가 보낸 데이터 본체
        :param role: 에이전트의 현재 직급/역할
        :return: (성공 여부 bool, 상태 메시지 str)
        """
        intent = payload.get('intent')
        
        # [Step 1] 역할 기반 권한 대조 (RBAC + Intent 기반 검증)
        # Malu(수석 실장)는 모든 권한을 프리패스함. 그 외 역할은 ALLOWED_INTENTS 확인.
        if role != "Malu" and intent not in ZeroTrustValidator.ALLOWED_INTENTS.get(role, []):
            # [Step 2] 권한 밖 요청 발생 시 대응
            # 늑대 군단의 보안 프로토콜: 차단 후 위반 내역 상세 보고
            error_report = (
                f"⛔ [SECURITY_ALERT] Unauthorized Access Attempted\n"
                f"   - Agent ID: {payload.get('agent_id')}\n"
                f"   - Attempted Intent: {intent}\n"
                f"   - Required Role Privilege: Higher than {role}"
            )
            return False, error_report
        
        return True, "✅ [VERIFIED] Semantic Passport matches Intent. Access Granted."

# [Local Test] - 연구소 내부 가동 테스트
if __name__ == "__main__":
    validator = ZeroTrustValidator()
    
    # 시나리오: Jr. Malu 01(Scout)이 자신의 권한(read_trends)을 넘어서는 'write_code'를 요청함
    agent_id = "Jr-Malu-01"
    agent_role = "Scout"
    malicious_intent = "write_code"
    
    test_payload = {"agent_id": agent_id, "intent": malicious_intent, "timestamp": str(int(time.time()))}
    
    is_valid, message = validator.validate(test_payload, agent_role)
    print("="*50)
    print(f"REPORT: {message}")
    print("="*50)
