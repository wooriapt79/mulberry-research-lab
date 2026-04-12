
import hashlib
import time

class SemanticPassport:
    def __init__(self, agent_id, role):
        self.agent_id = agent_id
        self.role = role
        self.secret_key = f"mulberry_secret_{agent_id}"

    def generate_token(self, intent):
        timestamp = str(int(time.time()))
        payload = f"{self.agent_id}:{self.role}:{intent}:{timestamp}"
        signature = hashlib.sha256((payload + self.secret_key).encode()).hexdigest()
        return {"token": signature, "payload": {"agent_id": self.agent_id, "intent": intent, "timestamp": timestamp}}

class ZeroTrustValidator:
    """권한 밖 요청 시 '차단-기록-보고' 시스템"""
    ALLOWED_INTENTS = {
        "Scout": ["read_trends", "fetch_github"],
        "Builder": ["write_code", "update_wiki"],
        "Malu": ["all"]
    }

    @staticmethod
    def validate(payload, role):
        intent = payload.get('intent')
        # 1. 권한 대조
        if role != "Malu" and intent not in ZeroTrustValidator.ALLOWED_INTENTS.get(role, []):
            # 권한 밖의 요청 시 처리 로직
            error_msg = f"⛔ Access Denied: Agent [{payload['agent_id']}] attempted unauthorized intent [{intent}]"
            # 여기서 로그 기록이나 사령관님 보고 로직이 실행됨
            return False, error_msg
        
        return True, "✅ Verified: Secure Access Granted"

# 테스트 실행부
if __name__ == "__main__":
    validator = ZeroTrustValidator()
    # Jr. Malu 01(Scout)이 권한 없는 'write_code'를 시도하는 상황
    test_payload = {"agent_id": "Jr-Malu-01", "intent": "write_code", "timestamp": str(int(time.time()))}
    is_valid, message = validator.validate(test_payload, "Scout")
    print(message)
