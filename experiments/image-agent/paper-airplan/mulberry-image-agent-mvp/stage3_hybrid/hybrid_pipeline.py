# stage3_hybrid/hybrid_pipeline.py
"""
Stage 3: Model 2 + Model 3 하이브리드 파이프라인
한국어 감성 프롬프트(Model 3) + 이중 메타데이터(Model 2)
→ 자연스러움 + 안정성 + 대용량 지원
"""

import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger("HybridPipeline")


class HybridPipeline:
    """
    Model 2 + Model 3 최적 조합

    흐름:
    KoreanPromptBuilder → DALL-E → Model3 메타데이터 삽입
    → MetadataEncoder (Model 2 보조 삽입) → QR 합성 → 배포
    """

    def __init__(self, openai_api_key: str = None, output_dir: str = "output/hybrid"):
        import sys, os
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from stage1_model2_mvp.metadata_encoder import MetadataEncoder, MetadataDecoder
        from stage1_model2_mvp.qr_distributor import QRDistributor
        from stage2_model3_korean.korean_prompt_builder import KoreanPromptBuilder
        from stage2_model3_korean.metadata_injector import Model3Generator

        self.prompt_builder = KoreanPromptBuilder()
        self.model3_generator = Model3Generator(
            api_key=openai_api_key,
            output_dir=f"{output_dir}/images",
        )
        self.encoder = MetadataEncoder()
        self.decoder = MetadataDecoder()
        self.distributor = QRDistributor(output_dir=f"{output_dir}/qr")

    def run(
        self,
        campaign: Dict,
        season: str = None,
        promotion_type: str = "cooperative_purchase",
        extra_keywords: list = None,
    ) -> Dict:
        """
        하이브리드 파이프라인 실행

        Args:
            campaign: 공동구매 캠페인 정보
            season: 계절 (None이면 자동 감지)
            promotion_type: 프로모션 유형
            extra_keywords: 추가 감성 키워드

        Returns:
            완성된 배포 패키지
        """
        import hashlib
        from datetime import datetime

        logger.info("=== Hybrid Pipeline 시작 ===")

        # 구매 코드 사전 생성 (Model 2/3 공통 사용)
        raw = f"{campaign['product']}:{campaign['campaign_id']}:{datetime.now().strftime('%Y%m%d')}"
        purchase_code = hashlib.sha256(raw.encode()).hexdigest()[:12].upper()

        # 계절 자동 감지
        if not season:
            month = datetime.now().month
            season = (
                "spring" if month in (3, 4, 5) else
                "summer" if month in (6, 7, 8) else
                "autumn" if month in (9, 10, 11) else
                "winter"
            )

        # [1단계] 한국어 감성 프롬프트 빌드 (Model 3)
        logger.info("[1/5] 한국어 감성 프롬프트 생성...")
        prompt_result = self.prompt_builder.build(
            product=campaign["product"],
            product_kr=campaign.get("product_kr", campaign["title"]),
            season=season,
            promotion_type=promotion_type,
            extra_keywords=extra_keywords or ["정겨운", "이웃", "함께"],
        )

        # [2단계] DALL-E 생성 + Model 3 메타데이터 즉시 삽입
        logger.info("[2/5] DALL-E 이미지 생성 + Model 3 메타데이터 삽입...")
        model3_result = self.model3_generator.generate_and_inject(
            prompt_result=prompt_result,
            campaign=campaign,
            purchase_code=purchase_code,
        )

        # [3단계] Model 2 보조 메타데이터 삽입 (이중 안전망)
        # Model 3 메타데이터가 플랫폼에서 제거되어도 Model 2로 복구 가능
        logger.info("[3/5] Model 2 보조 메타데이터 삽입...")
        encoded_path, _ = self.encoder.encode(
            image_path=model3_result["local_path"],
            campaign=campaign,
            output_path=model3_result["local_path"],  # 동일 파일에 추가
        )

        # [4단계] QR 합성
        logger.info("[4/5] QR코드 생성 및 합성...")
        qr_path = self.distributor.generate_qr(
            url=campaign["cta_url"],
            purchase_code=purchase_code,
        )
        final_image = encoded_path
        if qr_path:
            final_image = self.distributor.compose_with_qr(
                promo_image_path=encoded_path,
                qr_image_path=qr_path,
            )

        # [5단계] SMS 패키지 준비
        logger.info("[5/5] SMS 배포 패키지 준비...")
        sms_package = self.distributor.prepare_sms_package(
            image_path=final_image,
            purchase_code=purchase_code,
            cta_url=campaign["cta_url"],
            product_name=campaign["title"],
            price=campaign["price"],
            deadline=campaign.get("deadline", ""),
        )

        # 검증: 메타데이터 정상 삽입 확인
        verified = self.decoder.decode(final_image)
        is_valid = verified is not None

        result = {
            "status": "success" if is_valid else "warning",
            "purchase_code": purchase_code,
            "final_image": final_image,
            "qr_image": qr_path,
            "season": season,
            "promotion_type": promotion_type,
            "revised_prompt": model3_result.get("revised_prompt", ""),
            "keywords_used": prompt_result.get("keywords_used", []),
            "metadata_verified": is_valid,
            "sms_package": sms_package,
            "campaign_id": campaign["campaign_id"],
            "models_used": ["model2", "model3"],
        }

        logger.info(
            "=== Hybrid Pipeline 완료 — code=%s verified=%s ===",
            purchase_code, is_valid
        )
        return result


# ─────────────────────────────────────────
# 실행 예시
# ─────────────────────────────────────────
if __name__ == "__main__":
    pipeline = HybridPipeline()

    campaign = {
        "product": "potato",
        "product_kr": "인제 감자",
        "campaign_id": "INJE-2026-05",
        "title": "인제 감자 공동구매",
        "price": 15000,
        "min_participants": 10,
        "deadline": "2026-05-31",
        "cta_url": "https://mulberry.inje/join/potato-05",
        "organizer": "인제군 농협",
    }

    result = pipeline.run(
        campaign=campaign,
        season="spring",
        promotion_type="cooperative_purchase",
        extra_keywords=["정겨운", "인제", "공동구매"],
    )

    print("\n" + "=" * 55)
    print("Hybrid Pipeline 완성")
    print("=" * 55)
    print(f"구매 코드    : {result['purchase_code']}")
    print(f"최종 이미지  : {result['final_image']}")
    print(f"사용 키워드  : {result['keywords_used']}")
    print(f"메타 검증    : {result['metadata_verified']}")
    print(f"적용 모델    : {result['models_used']}")
    print(f"\nSMS 내용:\n{result['sms_package']['sms_text']}")
