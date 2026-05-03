# tests/test_pipeline.py
"""
메타데이터 인코더/디코더 단위 테스트 (API 호출 없이 실행 가능)
"""

import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PIL import Image
from PIL.PngImagePlugin import PngInfo
from stage1_model2_mvp.metadata_encoder import MetadataEncoder, MetadataDecoder
from stage1_model2_mvp.qr_distributor import QRDistributor
from stage2_model3_korean.korean_prompt_builder import KoreanPromptBuilder


def make_test_image(path: str):
    """테스트용 흰색 PNG 이미지 생성"""
    img = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
    img.save(path, "PNG")


def test_metadata_encode_decode():
    """메타데이터 삽입 → 추출 라운드트립 검증"""
    encoder = MetadataEncoder()
    decoder = MetadataDecoder()

    campaign = {
        "product": "potato",
        "campaign_id": "TEST-001",
        "title": "인제 감자 공동구매",
        "price": 15000,
        "min_participants": 10,
        "deadline": "2026-05-31",
        "cta_url": "https://mulberry.inje/join/test",
        "organizer": "테스트 농협",
    }

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name

    make_test_image(tmp_path)
    encoded_path, purchase_code = encoder.encode(tmp_path, campaign)

    result = decoder.decode(encoded_path)

    assert result is not None, "메타데이터 추출 실패"
    assert result["purchase_code"] == purchase_code, "코드 불일치"
    assert result["product"] == "potato"
    assert result["price"] == 15000
    assert result["version"] == "mulberry-v1"

    os.unlink(tmp_path)
    print(f"[PASS] 메타데이터 인코딩/디코딩: code={purchase_code}")


def test_cta_url_extraction():
    """CTA URL 빠른 추출 테스트"""
    encoder = MetadataEncoder()
    decoder = MetadataDecoder()

    campaign = {
        "product": "corn",
        "campaign_id": "TEST-002",
        "title": "인제 옥수수",
        "price": 8000,
        "cta_url": "https://mulberry.inje/join/corn-test",
        "organizer": "테스트",
    }

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name

    make_test_image(tmp_path)
    encoder.encode(tmp_path, campaign)

    url = decoder.get_cta_url(tmp_path)
    assert url == "https://mulberry.inje/join/corn-test"

    os.unlink(tmp_path)
    print(f"[PASS] CTA URL 추출: {url}")


def test_non_mulberry_image():
    """Mulberry 메타데이터 없는 이미지 처리"""
    decoder = MetadataDecoder()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name

    make_test_image(tmp_path)
    result = decoder.decode(tmp_path)

    assert result is None, "빈 이미지가 None을 반환해야 함"

    os.unlink(tmp_path)
    print("[PASS] 비멀베리 이미지 처리 정상")


def test_korean_prompt_builder_spring():
    """봄 인제 감자 프롬프트 생성"""
    builder = KoreanPromptBuilder()
    result = builder.build(
        product="potato",
        product_kr="인제 감자",
        season="spring",
        promotion_type="cooperative_purchase",
        extra_keywords=["정겨운", "이웃", "공동구매"],
    )

    assert "prompt" in result
    assert len(result["prompt"]) > 50
    assert result["season"] == "spring"
    assert result["product"] == "potato"
    assert isinstance(result["keywords_used"], list)

    print(f"[PASS] 한국어 프롬프트 생성 ({len(result['prompt'])}자)")
    print(f"       키워드: {result['keywords_used']}")


def test_korean_prompt_all_seasons():
    """4계절 프롬프트 모두 생성 확인"""
    builder = KoreanPromptBuilder()
    for season in ("spring", "summer", "autumn", "winter"):
        result = builder.build(
            product="mushroom",
            product_kr="산나물",
            season=season,
        )
        assert result["prompt"], f"{season} 프롬프트 생성 실패"
    print("[PASS] 4계절 프롬프트 전체 생성")


def test_sms_package_content():
    """SMS 패키지 내용 검증"""
    distributor = QRDistributor()
    pkg = distributor.prepare_sms_package(
        image_path="/tmp/test.png",
        purchase_code="ABC123DEF456",
        cta_url="https://mulberry.inje/join/test",
        product_name="인제 감자 공동구매",
        price=15000,
        deadline="2026-05-31",
    )

    assert "ABC123DEF456" in pkg["sms_text"]
    assert "15,000" in pkg["sms_text"]
    assert "2026-05-31" in pkg["sms_text"]
    assert pkg["char_count"] > 0

    print(f"[PASS] SMS 패키지: {pkg['char_count']}자")
    print(f"내용 미리보기:\n{pkg['sms_text']}")


if __name__ == "__main__":
    print("=" * 55)
    print("Mulberry Image Agent MVP 테스트")
    print("=" * 55)
    test_metadata_encode_decode()
    test_cta_url_extraction()
    test_non_mulberry_image()
    test_korean_prompt_builder_spring()
    test_korean_prompt_all_seasons()
    test_sms_package_content()
    print("=" * 55)
    print("모든 테스트 통과")
