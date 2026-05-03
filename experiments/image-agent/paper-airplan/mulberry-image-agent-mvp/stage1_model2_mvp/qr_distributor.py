# stage1_model2_mvp/qr_distributor.py
"""
QR코드 생성 및 SMS 배포 준비
공동구매 CTA URL → QR → 이미지에 합성
"""

import logging
from pathlib import Path
from typing import Optional
from PIL import Image

logger = logging.getLogger("QRDistributor")


class QRDistributor:
    """QR코드 생성 + 프로모션 이미지 합성"""

    def __init__(self, output_dir: str = "output/qr"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_qr(self, url: str, purchase_code: str) -> str:
        """CTA URL → QR코드 이미지 생성"""
        try:
            import qrcode

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2,
            )
            qr.add_data(url)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="#2C3E50", back_color="white")
            out_path = self.output_dir / f"qr_{purchase_code}.png"
            qr_img.save(out_path)
            logger.info("QR 생성 완료: %s", out_path)
            return str(out_path)

        except ImportError:
            logger.warning("qrcode 라이브러리 없음 — pip install qrcode[pil]")
            return None

    def compose_with_qr(
        self,
        promo_image_path: str,
        qr_image_path: str,
        output_path: str = None,
        position: str = "bottom-right",
        qr_size_ratio: float = 0.22,
    ) -> str:
        """
        프로모션 이미지 우하단에 QR코드 합성

        Args:
            position: "bottom-right" | "bottom-left" | "top-right"
            qr_size_ratio: QR코드 크기 비율 (전체 이미지 대비)
        """
        promo = Image.open(promo_image_path).convert("RGBA")
        qr = Image.open(qr_image_path).convert("RGBA")

        # QR 크기 조정
        qr_size = int(min(promo.width, promo.height) * qr_size_ratio)
        qr = qr.resize((qr_size, qr_size), Image.LANCZOS)

        # 위치 계산
        margin = 20
        positions = {
            "bottom-right": (promo.width - qr_size - margin, promo.height - qr_size - margin),
            "bottom-left":  (margin, promo.height - qr_size - margin),
            "top-right":    (promo.width - qr_size - margin, margin),
        }
        pos = positions.get(position, positions["bottom-right"])

        promo.paste(qr, pos, qr)

        out = output_path or promo_image_path.replace(".png", "_with_qr.png")
        promo.save(out, "PNG")
        logger.info("QR 합성 완료: %s", out)
        return out

    def prepare_sms_package(
        self,
        image_path: str,
        purchase_code: str,
        cta_url: str,
        product_name: str,
        price: int,
        deadline: str,
    ) -> dict:
        """
        SMS 발송용 메시지 패키지 준비

        Returns:
            {sms_text, image_path, short_url_placeholder}
        """
        sms_text = (
            f"[인제군 공동구매]\n"
            f"{product_name} 특가 공동구매\n"
            f"참여가: {price:,}원\n"
            f"마감: {deadline}\n"
            f"참여코드: {purchase_code}\n"
            f"참여하기: {cta_url}"
        )

        return {
            "sms_text": sms_text,
            "image_path": image_path,
            "purchase_code": purchase_code,
            "cta_url": cta_url,
            "char_count": len(sms_text),
        }
