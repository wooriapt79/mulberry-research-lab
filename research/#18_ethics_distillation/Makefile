# Mulberry Research #18 -- Ethics-Aware Distillation

PYTHON     := python3
CONFIG     ?= configs/instruct_config.yaml
OUTPUT_DIR := data/distilled_traces/$(shell date +%Y%m%d_%H%M)
SEED       ?= 42
ISSUE      := 18

.PHONY: help setup clean experiment paper test link

help:
	@echo "Mulberry Research #18 -- 자동화 타겟"
	@echo "  make setup       -- 가상환경 + 의존성 설치"
	@echo "  make experiment  -- 실험 실행 (OUTPUT_DIR 자동 생성)"
	@echo "  make paper       -- 논문 초안 업데이트"
	@echo "  make test        -- 윤리 게이트 테스트"
	@echo "  make link        -- 이슈 #18 연동 확인"
	@echo "  make clean       -- 임시 파일 제거"

setup:
	$(PYTHON) -m venv venv-research
	. venv-research/bin/activate && pip install -r requirements.txt
	@echo "Setup complete."

experiment:
	mkdir -p $(OUTPUT_DIR)
	$(PYTHON) -m experiments.distillation.run \
		--config $(CONFIG) \
		--output $(OUTPUT_DIR) \
		--seed $(SEED)
	@echo "Results saved to $(OUTPUT_DIR)"

paper:
	$(PYTHON) scripts/generate_paper_draft.py \
		--issue $(ISSUE) \
		--input data/distilled_traces/ \
		--output paper/sections/

test:
	$(PYTHON) -m pytest tests/ethics/ -v --cov=src/mulberry_edge/ethics

link:
	$(PYTHON) ../../scripts/link_issue_to_code.py --dry-run

clean:
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
	@echo "Clean complete."
