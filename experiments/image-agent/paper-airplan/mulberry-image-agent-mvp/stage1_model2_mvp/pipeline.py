# stage1_model2_mvp/pipeline.py
"""
Stage 1 MVP 전체 파이프라인
이미지 생성 → 메타데이터 삽입 → QR 합성 → 배포 패키지 준비
"""

import logging
from typing import Dict, Optional
from .image_generator import InjеImageGenerator
from .metadata_encoder import MetadataEncoder, MetadataDecoder
from .qr_distributor import QRDistributor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Stage1Pipeline")


class Stage1Pipeline:
    """
    Model 2 MVP 파이프라인
    인제군 공동구매 프로모션 이미지 생성부터 배포 패키지까지
    """

    def __init__(self, openai_api_key: str = None, output_dir: str = "output"):
        self.generator = InjеImageGenerator(
            api_key=openai_api_key,
            output_dir=f"{output_dir}/images",
        )
        self.encoder = MetadataEncoder()
        self.decoder = MetadataDecoder()
        self.distributor = QRDistributor(output_dir=f"{output_dir}/qr")

    def run(self, campaign: Dict, season: str = None) -> Dict:
        """
        전체 파이프라인 실행

        Args:
            campaign: {
                "product": "potato",
                "campaign_id": "INJE-2026-05",
                "title": "인제 감자 공동구매",
                "price": 15000,
                "min_participants": 10,
                "deadline": "2026-05-31",
                "cta_url": "https://mulberry.inje/join/potato-05",
                "organizer": "인제군 농협",
            }
            season: "spring"|"summer"|"autumn"|"winter" (None이면 자동 감지)

        Returns:
            완성된 배포 패키지 정보
        """
        logger.info("=== Stage1 파이프라인 시작 ===")

        # 1단계: 이미지 생성
        logger.info("[1/4] DALL-E 이미지 생성 중...")
        image_result = self.generator.generate(
            product=campaign["product"],
            season=season,
        )

        # 2단계: 메타데이터 삽입
        logger.info("[2/4] PNG 메타데이터 삽입 중...")
        encoded_path, purchase_code = self.encoder.encode(
            image_path=image_result["local_path"],
            campaign=campaign,
        )

        # 3단계: QR코드 생성 + 합성
        logger.info("[3/4] QR코드 생성 및 합성 중...")
        qr_path = self.distributor.generate_qr(
            url=campaign["cta_url"],
            purchase_code=purchase_code,
        )
        final_image_path = encoded_path
        if qr_path:
            final_image_path = self.distributor.compose_with_qr(
                promo_image_path=encoded_path,
                qr_image_path=qr_path,
            )

        # 4단계: SMS 패키지 준비
        logger.info("[4/4] SMS 배포 패키지 준비 중...")
        sms_package = self.distributor.prepare_sms_package(
            image_path=final_image_path,
            purchase_code=purchase_code,
            cta_url=campaign["cta_url"],
            product_name=campaign["title"],
            price=campaign["price"],
            deadline=campaign.get("deadline", ""),
        )

        # 검증: 메타데이터 정상 삽입 확인
        verified = self.decoder.decode(final_image_path)
        is_valid = verified is not None and verified["purchase_code"] == purchase_code

        result = {
            "status": "success" if is_valid else "warning",
            "purchase_code": purchase_code,
            "final_image": final_image_path,
            "qr_image": qr_path,
            "sms_package": sms_package,
            "metadata_verified": is_valid,
            "season": image_result["season"],
            "campaign_id": campaign["campaign_id"],
        }

        logger.info(
            "=== 파이프라인 완료 — code=%s verified=%s ===",
            purchase_code, is_valid
        )
        return result

    def decode_image(self, image_path: str) -> Optional[Dict]:
        """수신된 이미지에서 공동구매 정보 추출 (수신자 측)"""
        return self.decoder.decode(image_path)


# ─────────────────────────────────────────
# 실행 예시
# ─────────────────────────────────────────
if __name__ == "__main__":
    pipeline = Stage1Pipeline()

    campaign = {
        "product": "potato",
        "campaign_id": "INJE-2026-05",
        "title": "인제 감자 공동구매",
        "price": 15000,
        "min_participants": 10,
        "deadline": "2026-05-31",
        "cta_url": "https://mulberry.inje/join/potato-05",
        "organizer": "인제군 농협",
    }

    result = pipeline.run(campaign, season="spring")

    print("\n" + "=" * 50)
    print("배포 패키지 완성")
    print("=" * 50)
    print(f"구매 코드  : {result['purchase_code']}")
    print(f"최종 이미지: {result['final_image']}")
    print(f"메타 검증  : {result['metadata_verified']}")
    print(f"\nSMS 내용:\n{result['sms_package']['sms_text']}")
