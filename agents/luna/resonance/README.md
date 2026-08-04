# 🔮 Luna Resonance AI — LoRA Finetuning Package

Mulberry Project Luna의 감성 공명(Resonance) 추론을 위한 LoRA 파인튜닝 패키지입니다.

## 📁 파일 구성

| 파일 | 설명 |
|------|------|
| `finetune.py` | LoRA 학습 메인 스크립트 |
| `resonance_finetuning_dataset_v2.jsonl` | 학습 데이터셋 (155개 샘플) |
| `requirements.txt` | Python 패키지 목록 |
| `run_finetune.sh` | 원클릭 실행 셸 스크립트 |
| `.env.example` | 환경변수 템플릿 |

## ⚡ 빠른 시작

```bash
# 1. 환경변수 설정
cp .env.example .env
# .env에서 HF_TOKEN 입력

# 2. 실행 (자동으로 패키지 설치 → 학습 시작)
bash run_finetune.sh
```

## 🤖 모델 스펙

- **베이스 모델**: `mistralai/Mistral-7B-v0.1` (HF 승인 불필요)
- **LoRA**: r=16, alpha=32, target=q/v/k/o_proj
- **데이터**: 155개 샘플, 9:1 train/val split
- **출력**: `./lora-resonance-v2/`

## 📊 데이터셋 스키마

```json
{
  "user_input": "사용자 발화",
  "selected_card": "타로 카드명",
  "emotion_label": "Hope/Vulnerability",
  "emotion_vector": [0.8, 0.2, 0.1, 0.9],
  "recommended_product": "추천 상품",
  "resonance_score": 0.92,
  "purchase_made": true
}
```

## 🖥️ 권장 환경

- GPU: VRAM 16GB+ (A100, RTX 3090 이상)
- RAM: 32GB+
- Python: 3.10+
- 학습 시간: 약 2~4시간 (A100 기준)

---
*Mulberry Project — TRANG Manager, 2026-08-05*
