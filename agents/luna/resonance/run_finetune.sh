#!/bin/bash
# Resonance AI LoRA Finetuning Runner — Mulberry Project
# 수정: TRANG Manager 2026-08-05
# 데이터셋 v2 (155개), 출력 lora-resonance-v2

set -e  # 오류 즉시 종료

echo "🚀 Resonance AI LoRA Finetuning v2"
echo "===================================="
echo "  Dataset : resonance_finetuning_dataset_v2.jsonl (155개)"
echo "  Model   : Mistral-7B-v0.1 (기본값, HF 승인 불필요)"
echo "  Output  : ./lora-resonance-v2"
echo ""

# ── 1. .env 확인 ──────────────────────────────────────────────
echo "🔑 Step 1: .env 확인..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env 없음 — .env.example 참고해서 생성하세요."
    echo "    Mistral-7B 사용 시 HF_TOKEN 없이도 동작합니다."
    echo "    cp .env.example .env  후 재실행"
    # HF_TOKEN 없이도 Mistral은 동작하므로 종료하지 않음
else
    echo "✅ .env 로드됨"
    export $(grep -v '^#' .env | xargs)
fi

# ── 2. 패키지 설치 ─────────────────────────────────────────────
echo ""
echo "🔧 Step 2: 패키지 설치..."
pip install -q -r requirements.txt

# ── 3. 데이터셋 확인 ──────────────────────────────────────────
echo ""
echo "📊 Step 3: 데이터셋 확인..."
DATASET="${DATASET_PATH:-resonance_finetuning_dataset_v2.jsonl}"

if [ ! -f "$DATASET" ]; then
    echo "❌ 데이터셋 없음: $DATASET"
    echo "   resonance_finetuning_dataset_v2.jsonl 파일이 같은 디렉토리에 있어야 합니다."
    exit 1
fi

SAMPLE_COUNT=$(wc -l < "$DATASET")
echo "✅ 데이터셋 확인: $SAMPLE_COUNT 샘플"

if [ "$SAMPLE_COUNT" -lt 10 ]; then
    echo "⚠️  샘플 수가 너무 적습니다 (최소 10개 필요)"
    exit 1
fi

# ── 4. GPU 확인 ───────────────────────────────────────────────
echo ""
echo "🖥️  Step 4: GPU 확인..."
python -c "import torch; print('✅ CUDA' if torch.cuda.is_available() else '⚠️  CPU 모드 (속도 매우 느림)')"

# ── 5. 학습 시작 ──────────────────────────────────────────────
echo ""
echo "🔥 Step 5: LoRA 파인튜닝 시작..."
MODEL="${MODEL_NAME:-mistralai/Mistral-7B-v0.1}"
echo "   모델   : $MODEL"
echo "   에폭   : 5"
echo "   배치   : 2 (gradient_accumulation=4, 실효 배치=8)"
echo ""

python finetune.py

# ── 6. 결과 확인 ──────────────────────────────────────────────
OUTPUT="${OUTPUT_DIR:-./lora-resonance-v2}"
echo ""
echo "✅ LoRA 어댑터 저장 완료!"
echo ""
echo "📦 저장 위치: $OUTPUT"
ls -lah "$OUTPUT" 2>/dev/null || echo "(아직 출력 디렉토리 없음)"

echo ""
echo "🎉 파인튜닝 완료!"
echo ""
echo "📝 Next steps:"
echo "   1. 검증  : ls -la $OUTPUT"
echo "   2. 배포  : cp -r $OUTPUT /api/luna/resonance-inference/"
echo "   3. 테스트: python test_inference.py --model $OUTPUT"
