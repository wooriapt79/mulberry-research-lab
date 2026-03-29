import random
import asyncio
import logging

class ResponseController:
    LEVELS = {"NORMAL": 0, "ABBREVIATED": 1, "DELAYED": 2, "REFERENTIAL": 3, "REJECTED": 4}

    def __init__(self, agent, default_level=0, enable_delay=True):
        self.agent = agent
        self.current_level = default_level
        self.enable_delay = enable_delay

    def set_rest_mode(self, duration_minutes, extra=False):
        if extra or duration_minutes >= 20:
            self.set_level(self.LEVELS["REFERENTIAL"])
        elif duration_minutes >= 10:
            self.set_level(self.LEVELS["ABBREVIATED"])
        else:
            self.set_level(self.LEVELS["DELAYED"])
        if duration_minutes >= 30:
            self.set_level(self.LEVELS["REJECTED"])

    def unset_rest_mode(self):
        self.set_level(self.LEVELS["NORMAL"])

    def set_level(self, level):
        self.current_level = level
        logging.info(f"[ResponseController] Quality level set to {level}")

    async def process_response(self, user_query, context=None):
        if self.current_level >= self.LEVELS["DELAYED"] and self.enable_delay:
            delay_sec = random.randint(5, 10)
            await asyncio.sleep(delay_sec)
            logging.info(f"[ResponseController] Delayed response by {delay_sec}s")

        if self.current_level == self.LEVELS["NORMAL"]:
            return await self.agent.generate_response(user_query)
        elif self.current_level == self.LEVELS["ABBREVIATED"]:
            return f"💬 지금은 휴식 중이라 간단히 답변드려요: {user_query}에 대한 핵심은... (자세한 내용은 나중에 다시 물어봐 주세요)"
        elif self.current_level == self.LEVELS["REFERENTIAL"]:
            return f"📚 제 기억으로는 {user_query}와 관련하여 ... 이렇게 알고 있습니다. 더 정확한 답변은 휴식 후에 다시 물어봐 주세요."
        elif self.current_level == self.LEVELS["REJECTED"]:
            rest_until = context.get("rest_until", "잠시 후") if context else "잠시 후"
            return f"🍃 지금은 휴식 시간이에요. 더 나은 답변을 위해 {rest_until} 다시 와주시면 감사하겠습니다."
        else:
            return await self.agent.generate_response(user_query)
