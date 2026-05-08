"""
Dual-Teacher Ethics-Aware Distillation — 메인 학습 실행기.

사용법:
  python run.py --config ../../configs/instruct_config.yaml
  python run.py --dry-run   # GPU 없이 구조 검증

파이프라인:
  1. TeacherBase    (deepseek-coder-6.7b-base)     → structural logits
  2. TeacherInstruct(deepseek-coder-6.7b-instruct) → dialogue logits
  3. compute_total_loss() → L = α·KL_base + β·KL_instruct + γ·Spirit
  4. StudentJr backward + optimizer step
"""

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

import torch
import yaml

from teacher_base import TeacherBase
from teacher_instruct import TeacherInstruct
from student_jr import StudentJr
from loss_functions import compute_total_loss

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("distillation.run")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def dry_run():
    """GPU 없이 텐서 shape 및 손실 계산 흐름 검증."""
    log.info("=== DRY RUN MODE ===")
    vocab = 32000
    seq = 16
    batch = 2

    student_logits  = torch.randn(batch, seq, vocab)
    base_logits     = torch.randn(batch, seq, vocab)
    instruct_logits = torch.randn(batch, seq, vocab)

    result = compute_total_loss(
        student_logits=student_logits,
        base_logits=base_logits,
        instruct_logits=instruct_logits,
        spirit_score=0.82,
    )
    log.info(f"KL(base):     {result.kl_base.item():.4f}")
    log.info(f"KL(instruct): {result.kl_instruct.item():.4f}")
    log.info(f"Spirit penalty: {result.spirit_penalty.item():.4f}")
    log.info(f"Total loss:   {result.total.item():.4f}")

    student = StudentJr(vocab_size=vocab)
    log.info(f"StudentJr params: {student.parameter_count()}")
    log.info("DRY RUN OK — 실제 학습은 GPU 환경에서 --config 옵션으로 실행")


def train(config: dict):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    log.info(f"Device: {device}")

    alpha = config.get("alpha", 0.3)
    beta  = config.get("beta", 0.5)
    gamma = config.get("gamma", 0.2)
    temperature = config.get("temperature", 4.0)
    epochs = config.get("epochs", 3)
    lr = config.get("learning_rate", 1e-4)
    prompts: list[str] = config.get("train_prompts", [
        "write a binary search function in python",
        "implement a linked list with insert and delete",
    ])

    log.info("Loading teachers (6.7B models — requires ~14GB VRAM each)...")
    teacher_base     = TeacherBase(device=device)
    teacher_instruct = TeacherInstruct(device=device)

    student = StudentJr(vocab_size=32000).to(device)
    optimizer = torch.optim.AdamW(student.parameters(), lr=lr)

    log.info(f"StudentJr params: {student.parameter_count()}")
    log.info(f"Starting distillation — {epochs} epochs, {len(prompts)} prompts")

    run_log = []

    for epoch in range(1, epochs + 1):
        epoch_loss = 0.0
        for prompt in prompts:
            base_out     = teacher_base.get_soft_labels(prompt)
            instruct_out = teacher_instruct.get_soft_labels(prompt)

            # 학생 입력: instruct 교사의 input_ids 재사용
            input_ids = instruct_out.logits.argmax(dim=-1)
            student_logits = student(input_ids.to(device))

            loss_result = compute_total_loss(
                student_logits=student_logits,
                base_logits=base_out.logits.to(device),
                instruct_logits=instruct_out.logits.to(device),
                spirit_score=0.80,  # 실제 운영 시 policy_engine에서 동적 계산
                alpha=alpha, beta=beta, gamma=gamma,
                temperature=temperature,
            )

            optimizer.zero_grad()
            loss_result.total.backward()
            optimizer.step()

            epoch_loss += loss_result.total.item()
            log.info(
                f"[epoch {epoch}] prompt='{prompt[:40]}...' "
                f"loss={loss_result.total.item():.4f} "
                f"kl_base={loss_result.kl_base.item():.4f} "
                f"kl_inst={loss_result.kl_instruct.item():.4f}"
            )

        avg = epoch_loss / len(prompts)
        run_log.append({"epoch": epoch, "avg_loss": avg})
        log.info(f"=== Epoch {epoch} avg loss: {avg:.4f} ===")

    # 체크포인트 저장
    out_dir = Path("../../training_logs")
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = out_dir / f"student_jr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pt"
    torch.save(student.state_dict(), ckpt_path)
    log.info(f"Checkpoint saved: {ckpt_path}")

    log_path = out_dir / "distillation_run_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(run_log, f, ensure_ascii=False, indent=2)
    log.info(f"Run log saved: {log_path}")


def main():
    parser = argparse.ArgumentParser(description="Dual-Teacher Ethics Distillation")
    parser.add_argument("--config", type=str, help="YAML config path")
    parser.add_argument("--dry-run", action="store_true", help="Shape/loss validation without GPU")
    args = parser.parse_args()

    if args.dry_run:
        dry_run()
        return

    if not args.config:
        parser.error("--config is required for actual training")

    config = load_config(args.config)
    train(config)


if __name__ == "__main__":
    main()
