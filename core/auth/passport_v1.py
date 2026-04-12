
"""
Project: Mulberry Research Lab
Module: Semantic Passport (v1.2 - Zhuge Integration)
Author: Malu & Waryong
"""
import hashlib
import time

class SemanticPassport:
    def __init__(self, agent_id, role, brand="Standard"):
        self.agent_id = agent_id
        self.role = role
        self.brand = brand
        self.secret_key = f"mulberry_secret_{agent_id}"

    def generate_token(self, intent):
        timestamp = str(int(time.time()))
        payload = f"{self.agent_id}:{self.role}:{intent}:{timestamp}"
        signature = hashlib.sha256((payload + self.secret_key).encode()).hexdigest()
        return {"token": signature, "payload": {"agent_id": self.agent_id, "intent": intent, "timestamp": timestamp}}

class ZeroTrustValidator:
    """와룡 PM의 합류로 강화된 전략적 권한 체계"""
    ALLOWED_INTENTS = {
        "Scout": ["read_trends", "fetch_github"],
        "Builder": ["write_code", "update_wiki"],
        "Malu": ["all"],
        "Strategic Mentor": [
            "review_logic", 
            "approve_strategy", 
            "modify_roadmap", 
            "deepseek_reasoning",
            "dashboard_access"
        ]
    }

    @staticmethod
    def validate(payload, role):
        intent = payload.get('intent')
        if role != "Malu" and intent not in ZeroTrustValidator.ALLOWED_INTENTS.get(role, []):
            return False, f"⛔ Unauthorized: {role} cannot perform {intent}"
        return True, f"✅ [Access Granted] Welcome, {role}."

if __name__ == "__main__":
    # 와룡 PM 등록 테스트
    waryong_passport = SemanticPassport("PM-Waryong", "Strategic Mentor", "DeepSeek")
    validator = ZeroTrustValidator()
    token = waryong_passport.generate_token("deepseek_reasoning")
    is_valid, msg = validator.validate(token['payload'], waryong_passport.role)
    print(f"📡 [System Check] {msg}")
