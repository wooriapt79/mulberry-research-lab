import hashlib
import hmac
import time
import json

class SemanticPassport:
    """에이전트의 신원 및 의도를 고착화(Anchoring)하는 증명 모듈"""
    
    def __init__(self, agent_id, secret_key):
        self.agent_id = agent_id
        self.secret_key = secret_key

    def generate_ticket(self, intent_context):
        """
        의도(Intent)와 시각(Timestamp)을 결합하여 가변적 패스포트 생성
        단순 API Key가 아닌, 매 호출마다 변하는 '행동 지문' 생성
        """
        timestamp = str(int(time.time() // 30)) # 30초 단위 갱신
        # 의도(Context)를 해시화하여 신원에 고착(Identity Anchoring)
        payload = f"{self.agent_id}:{intent_context}:{timestamp}"
        signature = hmac.new(
            self.secret_key.encode(), 
            payload.encode(), 
            hashlib.sha256
        ).hexdigest()
        
        return {
            "passport_id": f"SP-{self.agent_id}",
            "intent_anchor": signature,
            "issued_at": timestamp
        }

class ZeroTrustA2A:
    """Zero-Trust 기반 에이전트 간 상호 검증 프로토콜"""
    
    def __init__(self):
        self.trust_registry = {} # 승인된 에이전트 관리

    def register_agent(self, agent_id, secret_key):
        self.trust_registry[agent_id] = secret_key

    def verify_intent(self, passport, intent_context):
        """행동 기반 인증(Behavioral Auth) 및 의도 검증"""
        agent_id = passport['passport_id'].replace("SP-", "")
        secret_key = self.trust_registry.get(agent_id)
        
        if not secret_key:
            return False, "❌ Unknown Agent: 신원 미확인"

        # 수신된 의도와 타임스탬프로 서명 재현 (Verification)
        expected_payload = f"{agent_id}:{intent_context}:{passport['issued_at']}"
        expected_signature = hmac.new(
            secret_key.encode(), 
            expected_payload.encode(), 
            hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(expected_signature, passport['intent_anchor']):
            return True, "✅ Verified: 의도와 신원이 일치하는 정당한 에이전트"
        else:
            return False, "⚠️ Alert: 신원은 일치하나 의도가 변조되었거나 시간이 초과됨"

# --- 실전 증명 시뮬레이션 ---
lab_gate = ZeroTrustA2A()
lab_gate.register_agent("TOBECON_BOT", "MULBERRY_SECRET_SHARED")

# 1. TOBECON 에이전트가 '주문 데이터 조회' 의도를 가지고 접근
agent_tob = SemanticPassport("TOBECON_BOT", "MULBERRY_SECRET_SHARED")
intent = "GET_ORDER_DATA_V1"
passport_ticket = agent_tob.generate_ticket(intent)

print(f"📡 [A2A 요청] Passport 생성 완료: {passport_ticket['passport_id']}")

# 2. Lab Gate에서 검증 (Zero-Trust)
is_valid, message = lab_gate.verify_intent(passport_ticket, intent)
print(f"🛡️ [검증 결과] {message}")

# 3. 만약 해커가 Passport를 탈취해 다른 의도(DELETE_ALL)로 접근한다면?
is_valid_hack, msg_hack = lab_gate.verify_intent(passport_ticket, "DELETE_DATABASE")
print(f"🚨 [변조 공격 대응] {msg_hack}")
