# mulberry_connector/adapters/sns.py
"""
SNS Adapter — 외부 채널 연동 (CSA Kbin 설계)
Image -> OCR -> Intent -> Policy -> Post 파이프라인.
현재: 로그 출력 (실제 API 연동은 채널별 확장)
"""

from dataclasses import dataclass


@dataclass
class SNSResult:
    success: bool
    channel: str
    message: str


class SNSAdapter:
    """SNS 게시 어댑터 (확장 가능 구조)"""

    SUPPORTED = ["slack", "discord", "telegram", "log"]

    def post(self, channel: str, content: str, agent_id: str) -> SNSResult:
        if channel not in self.SUPPORTED:
            return SNSResult(success=False, channel=channel, message=f"미지원 채널: {channel}")

        if channel == "log":
            print(f"[SNS:{channel}] [{agent_id}] {content[:100]}")
            return SNSResult(success=True, channel=channel, message="로그 출력 완료")

        # 실제 채널 연동은 환경변수 기반 확장
        print(f"[SNS:{channel}] [{agent_id}] 전송 준비 (API 키 필요)")
        return SNSResult(success=False, channel=channel, message="API 키 미설정")
