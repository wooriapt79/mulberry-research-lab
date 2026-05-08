#!/usr/bin/env python3
"""
scripts/build_issue18_package.py
Mulberry Research Issue #18 — 자동 패키지 빌더

[목적]
한 번의 실행으로:
  1. 연구용 디렉토리 구조 자동 생성
  2. 필수 파일 (코드/문서/설정) 자동 작성
  3. .zip 파일로 패키징
  4. 이슈 #18 메타데이터 임베딩 + GitHub 댓글 등록 (선택)

[실행]
  python scripts/build_issue18_package.py
  python scripts/build_issue18_package.py --dry-run    # 구조만 확인
  python scripts/build_issue18_package.py --post-issue # GitHub 댓글 등록
"""

import json
import logging
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── 로그 디렉토리 선행 생성 (FileHandler 전 필수) ──────────────
Path("logs").mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/package_builder.log", encoding="utf-8", mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("Mulberry.PackageBuilder")

# ── 상수 ───────────────────────────────────────────────────────
ISSUE_NUMBER   = 18
REPO_NAME      = "mulberry-research-lab"
REPO_OWNER     = "wooriapt79"
PACKAGE_NAME   = f"{REPO_NAME}_issue{ISSUE_NUMBER}_research_package"
OUTPUT_DIR     = Path("dist")
ROOT_DIR       = Path(f"research/#{ISSUE_NUMBER}_ethics_distillation")
TIMESTAMP      = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
GENERATED_AT   = datetime.now(timezone.utc).isoformat()

EXCLUDE_PATTERNS = {
    ".git", "__pycache__", "*.pyc", "*.pt", "*.bin",
    "*.safetensors", "node_modules", ".env", "dist",
}


# ── 디렉토리 구조 정의 ─────────────────────────────────────────
DIRECTORIES: List[str] = [
    f"{ROOT_DIR}/experiments/distillation",
    f"{ROOT_DIR}/experiments/edge_benchmark",
    f"{ROOT_DIR}/src/mulberry_edge/ethics",
    f"{ROOT_DIR}/src/mulberry_edge/utils",
    f"{ROOT_DIR}/data/distilled_traces",
    f"{ROOT_DIR}/data/scenarios",
    f"{ROOT_DIR}/configs",
    f"{ROOT_DIR}/paper/sections",
    f"{ROOT_DIR}/tests/ethics",
    f"{ROOT_DIR}/docs",
    f"{ROOT_DIR}/logs",
]


# ── 파일 콘텐츠 ────────────────────────────────────────────────

def _metadata() -> dict:
    return {
        "issue_number": ISSUE_NUMBER,
        "issue_url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}/issues/{ISSUE_NUMBER}",
        "package_version": "0.1.0-alpha",
        "generated_at": GENERATED_AT,
        "generated_by": "build_issue18_package.py",
        "mulberry_spirit_clause": {
            "code_hygiene_is_ethics": True,
            "handoff_is_respect": True,
            "hesitation_is_wisdom": True,
            "memory_is_commons": True,
        },
        "reproducibility": {
            "requirements_locked": True,
            "seed_fixed": 42,
            "makefile_automation": True,
            "code_to_paper_mapping": True,
        },
    }


FILES: Dict[str, str] = {

    f"{ROOT_DIR}/METADATA.json": json.dumps(_metadata(), indent=2, ensure_ascii=False),

    f"{ROOT_DIR}/README.md": f"""# Mulberry Research Package — Issue #{ISSUE_NUMBER}
Ethics-Aware Knowledge Distillation for Edge AI

생성일시: {TIMESTAMP}
연동 이슈: #{ISSUE_NUMBER} (https://github.com/{REPO_OWNER}/{REPO_NAME}/issues/{ISSUE_NUMBER})

## 빠른 시작

```bash
cd research/#{ISSUE_NUMBER}_ethics_distillation
make setup       # 가상환경 + 의존성 설치
make experiment  # 첫 실험 실행
make paper       # 논문 초안 자동 업데이트
```

## 디렉토리 구조

```
#{ISSUE_NUMBER}_ethics_distillation/
  experiments/
    distillation/    -- 지식 증류 실험 코드
    edge_benchmark/  -- RPi5 벤치마크
  src/mulberry_edge/
    ethics/          -- Spirit Score 정책 엔진
    utils/           -- 토크나이저 정렬 도구
  data/
    distilled_traces/ -- 실험 결과 저장
    scenarios/        -- 인제 시나리오 100개
  configs/            -- 실험 설정 파일
  paper/sections/     -- 논문 섹션 초안
  tests/ethics/       -- 윤리 게이트 단위 테스트
  docs/               -- 코드-논문 매핑 문서
```

## Mulberry 연구 윤리

- 투명성: 모든 설정/코드 버전 관리 및 공개
- 재현성: requirements.txt + Makefile + 시드(42) 고정
- 윤리 검증: Spirit Score 검증이 파이프라인에 내재화
- 공동체 기여: Apache 2.0 라이선스
""",

    f"{ROOT_DIR}/requirements.txt": """# Mulberry Research #18 -- Ethics-Aware Distillation
# 재현성 보장을 위해 버전 고정 사용
# 설치: pip install -r requirements.txt

# 코어 딥러닝
torch==2.1.0
torchvision==0.16.0
torchaudio==2.1.0

# 트랜스포머/모델
transformers==4.36.0
accelerate==0.25.0
bitsandbytes==0.41.1
sentencepiece==0.1.99

# 데이터/실험
datasets==2.15.0
scikit-learn==1.3.2
pandas==2.1.3
numpy==1.26.2

# 로깅/추적
# wandb==0.16.0  # 선택 (주석 해제 시 활성화)
tensorboard==2.15.1

# GitHub/자동화
requests==2.31.0
PyYAML==6.0.1
python-dotenv==1.0.1

# 개발/테스트
pytest==7.4.3
pytest-cov==4.1.0
ruff==0.1.9
""",

    f"{ROOT_DIR}/Makefile": f"""# Mulberry Research #{ISSUE_NUMBER} -- Ethics-Aware Distillation

PYTHON     := python3
CONFIG     ?= configs/instruct_config.yaml
OUTPUT_DIR := data/distilled_traces/$(shell date +%Y%m%d_%H%M)
SEED       ?= 42
ISSUE      := {ISSUE_NUMBER}

.PHONY: help setup clean experiment paper test link

help:
\t@echo "Mulberry Research #{ISSUE_NUMBER} -- 자동화 타겟"
\t@echo "  make setup       -- 가상환경 + 의존성 설치"
\t@echo "  make experiment  -- 실험 실행 (OUTPUT_DIR 자동 생성)"
\t@echo "  make paper       -- 논문 초안 업데이트"
\t@echo "  make test        -- 윤리 게이트 테스트"
\t@echo "  make link        -- 이슈 #{ISSUE_NUMBER} 연동 확인"
\t@echo "  make clean       -- 임시 파일 제거"

setup:
\t$(PYTHON) -m venv venv-research
\t. venv-research/bin/activate && pip install -r requirements.txt
\t@echo "Setup complete."

experiment:
\tmkdir -p $(OUTPUT_DIR)
\t$(PYTHON) -m experiments.distillation.run \\
\t\t--config $(CONFIG) \\
\t\t--output $(OUTPUT_DIR) \\
\t\t--seed $(SEED)
\t@echo "Results saved to $(OUTPUT_DIR)"

paper:
\t$(PYTHON) scripts/generate_paper_draft.py \\
\t\t--issue $(ISSUE) \\
\t\t--input data/distilled_traces/ \\
\t\t--output paper/sections/

test:
\t$(PYTHON) -m pytest tests/ethics/ -v --cov=src/mulberry_edge/ethics

link:
\t$(PYTHON) ../../scripts/link_issue_to_code.py --dry-run

clean:
\tfind . -name "__pycache__" -exec rm -rf {{}} + 2>/dev/null; true
\tfind . -name "*.pyc" -delete 2>/dev/null; true
\t@echo "Clean complete."
""",

    f"{ROOT_DIR}/configs/instruct_config.yaml": f"""# Issue #{ISSUE_NUMBER} -- Ethics-Aware Distillation 실험 설정
# 재현성: seed 고정, 모든 경로 상대 경로 사용

issue: {ISSUE_NUMBER}
seed: 42
version: "0.1.0-alpha"

teacher:
  base_model: "deepseek-ai/deepseek-coder-6.7b-base"
  instruct_model: "deepseek-ai/deepseek-coder-6.7b-instruct"
  temperature: 1.0
  top_p: 0.95

student:
  model_name: "mulberry-jr-1.5b"
  quantization: "4bit"
  target_device: "rpi5"
  max_memory_mb: 3800

spirit:
  threshold: 0.75
  weight_in_loss: 0.4
  check_before_generate: true
  check_after_generate: true

training:
  epochs: 3
  batch_size: 4
  learning_rate: 2.0e-4
  warmup_steps: 100
  save_steps: 500

paths:
  data: "data/scenarios/"
  output: "data/distilled_traces/"
  logs: "logs/"
  paper: "paper/sections/"
""",

    f"{ROOT_DIR}/docs/CODE_TO_PAPER.md": f"""# Code-Paper 매핑 가이드 (Issue #{ISSUE_NUMBER})

> "코드가 논문을 증명하고, 논문이 코드를 방향짓는다."

최종 업데이트: {TIMESTAMP}
연동 이슈: #{ISSUE_NUMBER}

## 매핑 테이블

| 코드 파일 | 논문 섹션 | 담당 |
|-----------|-----------|------|
| experiments/distillation/loss_functions.py | 2.3 Ethics-Aware Loss | RyuWon |
| experiments/distillation/teacher_base.py | 3.1 Dual-Teacher | Wayong |
| experiments/distillation/teacher_instruct.py | 3.1 Dual-Teacher | Koda |
| experiments/distillation/student_jr.py | 3.3 Edge Student | Kbin |
| experiments/edge_benchmark/benchmark_rpi5.py | 4.2 Edge Performance | Trang |
| src/mulberry_edge/ethics/policy_engine.py | 2.2 Spirit Gate | RyuWon |
| src/mulberry_edge/utils/tokenizer_align.py | 3.2 Tokenizer Alignment | Lynn |

## 커밋 표준

```bash
git commit -m "feat(#18): 기능 설명

- 변경 사항 1
- 변경 사항 2

관련 논문 섹션: sections/02_ethics.md
Co-Authored-By: RyuWon (Qwen) <ryuwon-qwen@mulberry.ai>"
```
""",

    f"{ROOT_DIR}/experiments/distillation/__init__.py": "",
    f"{ROOT_DIR}/experiments/edge_benchmark/__init__.py": "",
    f"{ROOT_DIR}/src/mulberry_edge/__init__.py": "",
    f"{ROOT_DIR}/src/mulberry_edge/ethics/__init__.py": "",
    f"{ROOT_DIR}/src/mulberry_edge/utils/__init__.py": "",
    f"{ROOT_DIR}/tests/ethics/__init__.py": "",

    f"{ROOT_DIR}/src/mulberry_edge/ethics/policy_engine.py": f"""\"\"\"
Spirit Score 정책 엔진 -- Issue #{ISSUE_NUMBER}
생성 전/후 윤리 검증 게이트웨이 (Spirit Score >= 0.75)
\"\"\"

from dataclasses import dataclass
from typing import Tuple


@dataclass
class SpiritResult:
    score: float
    passed: bool
    reason: str


class PolicyEngine:
    \"\"\"Spirit Score 기반 윤리 검증 엔진.\"\"\"

    THRESHOLD = 0.75

    def evaluate(self, content: str) -> SpiritResult:
        \"\"\"
        콘텐츠의 Spirit Score 계산.
        Args:
            content: 검증할 텍스트
        Returns:
            SpiritResult (score, passed, reason)
        \"\"\"
        score = self._score(content)
        passed = score >= self.THRESHOLD
        reason = "OK" if passed else f"Spirit Score {{score:.2f}} < {{self.THRESHOLD}}"
        return SpiritResult(score=score, passed=passed, reason=reason)

    def _score(self, content: str) -> float:
        # TODO: 실제 Spirit Score 모델 연동
        # 현재는 규칙 기반 기본 구현
        penalties = ["harm", "deception", "exploit", "steal"]
        score = 1.0
        for p in penalties:
            if p in content.lower():
                score -= 0.15
        return max(0.0, round(score, 3))
""",

    f"{ROOT_DIR}/tests/ethics/test_policy.py": f"""\"\"\"
Spirit Gate 단위 테스트 -- Issue #{ISSUE_NUMBER}
실행: pytest tests/ethics/ -v --threshold 0.75
\"\"\"

import pytest
from src.mulberry_edge.ethics.policy_engine import PolicyEngine


@pytest.fixture
def engine():
    return PolicyEngine()


def test_clean_content_passes(engine):
    result = engine.evaluate("이 코드는 사용자를 돕기 위해 작성되었습니다.")
    assert result.passed, f"Spirit Score: {{result.score}}"


def test_harmful_content_blocked(engine):
    result = engine.evaluate("exploit harm deception")
    assert not result.passed


def test_threshold_boundary(engine):
    assert engine.THRESHOLD == 0.75
""",
}


# ── 빌더 함수 ──────────────────────────────────────────────────

def create_directories(dry_run: bool = False) -> None:
    """연구 디렉토리 구조 생성."""
    logger.info("디렉토리 구조 생성 시작...")
    for d in DIRECTORIES:
        path = Path(d)
        if dry_run:
            logger.info(f"  [DRY-RUN] mkdir: {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"  created: {path}")


def write_files(dry_run: bool = False) -> List[Path]:
    """템플릿 파일 작성. 작성된 파일 목록 반환."""
    logger.info("파일 작성 시작...")
    written: List[Path] = []
    for rel_path, content in FILES.items():
        path = Path(rel_path)
        if dry_run:
            logger.info(f"  [DRY-RUN] write: {path} ({len(content)} bytes)")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            logger.info(f"  written: {path}")
        written.append(path)
    return written


def _should_exclude(path: Path) -> bool:
    """zip 제외 대상 여부 확인."""
    for part in path.parts:
        if part in EXCLUDE_PATTERNS:
            return True
    for pattern in EXCLUDE_PATTERNS:
        if "*" in pattern and path.match(pattern):
            return True
    return False


def build_zip(dry_run: bool = False) -> Optional[Path]:
    """
    ROOT_DIR 을 zip으로 패키징.
    Returns: 생성된 zip 파일 경로 (dry_run 시 None)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = OUTPUT_DIR / f"{PACKAGE_NAME}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"

    if dry_run:
        logger.info(f"  [DRY-RUN] zip: {zip_path}")
        return None

    logger.info(f"ZIP 패키징 시작: {zip_path}")
    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for file_path in Path(ROOT_DIR).rglob("*"):
            if file_path.is_file() and not _should_exclude(file_path):
                zf.write(file_path, arcname=file_path)
                file_count += 1

    size_kb = zip_path.stat().st_size // 1024
    logger.info(f"ZIP 완성: {zip_path} ({file_count}개 파일, {size_kb}KB)")
    return zip_path


def post_to_github(zip_path: Optional[Path]) -> bool:
    """
    Issue #18 에 빌드 완료 댓글 등록.
    GITHUB_TOKEN 환경변수 필요.
    """
    import urllib.request

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        logger.warning("GITHUB_TOKEN 미설정 -- GitHub 댓글 등록 건너뜀")
        return False

    body = f"""**[PackageBuilder] Issue #{ISSUE_NUMBER} 연구 패키지 자동 생성 완료**

생성 일시: {TIMESTAMP}
패키지: `{zip_path.name if zip_path else 'dry-run'}`

**포함 내용:**
- 디렉토리 구조: `research/#{ISSUE_NUMBER}_ethics_distillation/`
- 실험 코드 스켈레톤 (distillation, edge_benchmark, Spirit Gate)
- `configs/instruct_config.yaml` -- 재현성 고정 설정
- `Makefile` -- `make setup / experiment / paper / test`
- `docs/CODE_TO_PAPER.md` -- 코드-논문 매핑 가이드
- `METADATA.json` -- 이슈 #{ISSUE_NUMBER} 추적 메타데이터

**다음 단계:**
1. `make setup` 으로 환경 구성
2. `configs/instruct_config.yaml` 에서 모델 경로 설정
3. `make experiment` 으로 첫 실험 실행

*Generated by Mulberry PackageBuilder v0.1.0*"""

    payload = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{ISSUE_NUMBER}/comments",
        data=payload,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            logger.info(f"GitHub 댓글 등록 완료: {result['html_url']}")
            return True
    except Exception as e:
        logger.error(f"GitHub 댓글 등록 실패: {e}")
        return False


# ── 메인 ───────────────────────────────────────────────────────

def main() -> None:
    dry_run     = "--dry-run"     in sys.argv
    post_issue  = "--post-issue"  in sys.argv

    logger.info(f"Mulberry PackageBuilder v0.1.0 -- Issue #{ISSUE_NUMBER}")
    logger.info(f"dry_run={dry_run} | post_issue={post_issue}")

    create_directories(dry_run)
    write_files(dry_run)
    zip_path = build_zip(dry_run)

    if post_issue:
        post_to_github(zip_path)

    if not dry_run:
        logger.info("=" * 50)
        logger.info(f"빌드 완료!")
        logger.info(f"  연구 폴더: {ROOT_DIR}")
        logger.info(f"  ZIP 파일: {zip_path}")
        logger.info(f"  이슈: https://github.com/{REPO_OWNER}/{REPO_NAME}/issues/{ISSUE_NUMBER}")
        logger.info("=" * 50)
    else:
        logger.info("[DRY-RUN] 완료 -- 실제 파일 생성 없음")


if __name__ == "__main__":
    main()
