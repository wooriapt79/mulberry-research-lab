# Mulberry Image Endpoint Package

This package contains a minimal MVP for:

- Brand Registry schema (`brand_registry.json`)
- Intent Dictionary (`intent_dictionary.json`)
- OCR → Intent → Function FastAPI sample (`mulberry_image_endpoint_fastapi.py`)
- 3 test banners:
  - logo-based
  - hybrid
  - text-based

## Run

```bash
pip install fastapi uvicorn
uvicorn mulberry_image_endpoint_fastapi:app --reload
```

## Test API

```bash
curl -X POST http://127.0.0.1:8000/v1/intent/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "brand_id": "mulberry",
    "extracted_text": "보험 청구 도움을 요청합니다",
    "text_confidence": 0.98
  }'
```

## Core Concept

Image / Logo / Banner
→ OCR / visual recognition
→ Brand Registry lookup
→ Intent inference
→ Function mapping
→ Agent execution

## Notes

This package is designed as a safe prototype:
- no hidden command syntax
- no platform evasion logic
- natural-language intent mapping only