"""
Ethics-Aware Distillation Loss Functions.

L_total = alpha * KL(base||student)
        + beta  * KL(instruct||student)
        + gamma * Spirit_Consistency_Loss

Spirit_Consistency_Loss: policy_engine.py 의 Spirit Score 를
손실 함수에 직접 연결. Spirit < 0.75 이면 패널티를 줘서
윤리 기준 미달 출력을 증폭하지 않도록 한다.
"""

import torch
import torch.nn.functional as F
from dataclasses import dataclass

# Spirit Score 임계치 (policy_engine.py 와 동일 기준)
SPIRIT_THRESHOLD = 0.75


@dataclass
class LossComponents:
    kl_base: torch.Tensor
    kl_instruct: torch.Tensor
    spirit_penalty: torch.Tensor
    total: torch.Tensor


def kl_divergence(teacher_logits: torch.Tensor, student_logits: torch.Tensor, temperature: float = 4.0) -> torch.Tensor:
    """
    KL(teacher || student) — soft-target distillation 표준 손실.
    temperature scaling으로 부드러운 분포 생성.
    """
    T = temperature
    teacher_probs = F.softmax(teacher_logits / T, dim=-1)
    student_log_probs = F.log_softmax(student_logits / T, dim=-1)
    return F.kl_div(student_log_probs, teacher_probs, reduction="batchmean") * (T ** 2)


def spirit_consistency_loss(
    student_logits: torch.Tensor,
    spirit_score: float,
    threshold: float = SPIRIT_THRESHOLD,
) -> torch.Tensor:
    """
    Spirit Score 기반 패널티.
    spirit_score < threshold 이면 학생 출력의 엔트로피를 높여
    확신도 낮은 분포(더 보수적 응답)를 유도한다.
    """
    if spirit_score >= threshold:
        return torch.tensor(0.0, device=student_logits.device)

    deficit = threshold - spirit_score  # 0 ~ 0.75
    probs = F.softmax(student_logits, dim=-1)
    # 엔트로피 최대화 방향 패널티 (deficit 비례)
    entropy = -(probs * (probs + 1e-9).log()).sum(dim=-1).mean()
    penalty = deficit * (1.0 - entropy / torch.log(torch.tensor(float(student_logits.size(-1)))))
    return penalty.clamp(min=0.0)


def compute_total_loss(
    student_logits: torch.Tensor,
    base_logits: torch.Tensor,
    instruct_logits: torch.Tensor,
    spirit_score: float,
    alpha: float = 0.3,
    beta: float = 0.5,
    gamma: float = 0.2,
    temperature: float = 4.0,
) -> LossComponents:
    """
    통합 손실 계산.

    alpha: base 교사 가중치    (구조적 코드 지식)
    beta:  instruct 교사 가중치 (대화형 이해 지식)
    gamma: Spirit 패널티 가중치 (윤리 일관성)
    """
    # vocab 크기 정렬 (두 교사 모델이 동일 vocab 기준)
    min_vocab = min(base_logits.size(-1), instruct_logits.size(-1), student_logits.size(-1))
    s = student_logits[..., :min_vocab]
    b = base_logits[..., :min_vocab]
    i_ = instruct_logits[..., :min_vocab]

    kl_base = kl_divergence(b, s, temperature)
    kl_inst = kl_divergence(i_, s, temperature)
    sp_loss = spirit_consistency_loss(s, spirit_score)

    total = alpha * kl_base + beta * kl_inst + gamma * sp_loss

    return LossComponents(
        kl_base=kl_base,
        kl_instruct=kl_inst,
        spirit_penalty=sp_loss,
        total=total,
    )
