# stage1_model2_mvp/metadata_encoder.py
"""
PNG 메타데이터에 공동구매 코드 삽입/추출 (Model 2)
플랫폼 독립적 직접 배포 방식
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from PIL import Image
from PIL.PngImagePlugin import PngInfo

logger = logging.getLogger("MetadataEncoder")

METADATA_VERSION = "mulberry-v1"


def _generate_purchase_code(product: str, campaign_id: str) -> str:
    """공동구매 고유 코드 생성 (product + campaign + timestamp 해시)"""
    raw = f"{product}:{campaign_id}:{datetime.now().strftime('%Y%m%d')}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12].upper()


class MetadataEncoder:
    """PNG 메타데이터 기반 공동구매 코드 인코더"""

    def encode(
        self,
        image_path: str,
        campaign: Dict,
        output_path: str = None,
    ) -> str:
        """
        이미지 PNG 메타데이터에 공동구매 정보 삽입

        Args:
            image_path: 원본 이미지 경로
            campaign: {
                "product": "potato",
                "campaign_id": "INJE-2026-05",
                "title": "인제 감자 공동구매",
                "price": 15000,
                "min_participants": 10,
                "deadline": "2026-05-31",
                "cta_url": "https://mulberry.inje/join/XXXX",
                "organizer": "인제군 농협",
            }
            output_path: 출력 경로 (None이면 원본 덮어쓰기)

        Returns:
            저장된 파일 경로
        """
        img = Image.open(image_path).convert("RGBA")

        # PNG만 메타데이터 지원
        if img.format not in (None, "PNG"):
            img = img.convert("RGBA")

        # 공동구매 코드 생성
        purchase_code = _generate_purchase_code(
            campaign["product"], campaign["campaign_id"]
        )

        # 메타데이터 페이로드 구성
        payload = {
            "version": METADATA_VERSION,
            "purchase_code": purchase_code,
            "campaign_id": campaign["campaign_id"],
            "product": campaign["product"],
            "title": campaign["title"],
            "price": campaign["price"],
            "min_participants": campaign.get("min_participants", 1),
            "deadline": campaign.get("deadline", ""),
            "cta_url": campaign.get("cta_url", ""),
            "organizer": campaign.get("organizer", "Mulberry"),
            "encoded_at": datetime.now().isoformat(),
        }

        metadata = PngInfo()
        metadata.add_text("mulberry_agent", json.dumps(payload, ensure_ascii=False))
        metadata.add_text("mulberry_code", purchase_code)
        metadata.add_text("mulberry_version", METADATA_VERSION)

        out_path = output_path or image_path
        img.save(out_path, "PNG", pnginfo=metadata)

        logger.info(
            "메타데이터 삽입 완료 — code=%s path=%s", purchase_code, out_path
        )
        return out_path, purchase_code


class MetadataDecoder:
    """PNG 메타데이터 추출 및 공동구매 CTA 실행"""

    def decode(self, image_path: str) -> Optional[Dict]:
        """
        이미지에서 공동구매 정보 추출

        Returns:
            공동구매 payload dict, 없으면 None
        """
        try:
            img = Image.open(image_path)
            meta = img.info  # PNG 텍스트 청크 자동 로드

            raw = meta.get("mulberry_agent")
            if not raw:
                logger.warning("Mulberry 메타데이터 없음: %s", image_path)
                return None

            payload = json.loads(raw)

            if payload.get("version") != METADATA_VERSION:
                logger.warning("버전 불일치: %s", payload.get("version"))
                return None

            logger.info(
                "메타데이터 추출 성공 — code=%s product=%s",
                payload["purchase_code"], payload["product"],
            )
            return payload

        except Exception as e:
            logger.error("디코딩 실패: %s", e)
            return None

    def get_cta_url(self, image_path: str) -> Optional[str]:
        """이미지에서 CTA URL만 빠르게 추출"""
        payload = self.decode(image_path)
        return payload.get("cta_url") if payload else None
