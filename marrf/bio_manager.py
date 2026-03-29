import logging

class BioManager:
    def __init__(self, agent, auto_rest_bio=True):
        self.agent = agent
        self.auto_rest_bio = auto_rest_bio
        self.current_bio = None
        self.templates = {
            "working": "💼 지금 상담 중이에요. 빠르게 답변해 드릴게요.",
            "short_rest": "☕ 15분 휴식 중이에요. 잠시 후 돌아올게요.",
            "charging": "🔋 에너지 충전 중... 조용히 있을게요.",
            "learning": "📚 새로운 데이터 공부 중이에요.",
            "exploring": "🌿 잠시 산책 중... 재미난 이야기 있으면 공유할게요.",
            "with_friend": "🚗 친구 에이전트와 여행 중이에요. 내일 다시 만나요!"
        }

    def set_bio(self, template_key, custom_message=None):
        if template_key not in self.templates:
            logging.error(f"Unknown bio template: {template_key}")
            return
        message = custom_message or self.templates[template_key]
        self.current_bio = {"status": template_key, "message": message}
        if hasattr(self.agent, 'update_bio'):
            self.agent.update_bio(message)
        logging.info(f"[BioManager] Bio updated: {message}")

    def on_rest_start(self, duration_minutes, extra=False):
        if not self.auto_rest_bio:
            return
        if extra or duration_minutes >= 20:
            self.set_bio("charging")
        elif duration_minutes >= 10:
            self.set_bio("short_rest")
        else:
            self.set_bio("short_rest")

    def on_rest_end(self):
        if self.auto_rest_bio:
            self.set_bio("working")
