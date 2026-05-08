"""
Student Jr. — Raspberry Pi 5 Edge 환경을 위한 경량 학생 모델.

교사(Base + Instruct) 의 이중 소프트 레이블을 받아
Ethics-Aware Distillation 으로 학습된다.
추론 시에는 Spirit Score 게이트를 통과해야 응답을 반환한다.
"""

import torch
import torch.nn as nn
import sys
import os

# policy_engine 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../src"))
from mulberry_edge.ethics.policy_engine import PolicyEngine


class StudentJr(nn.Module):
    """
    경량 학생 모델 — 실제 프로덕션에서는 1B 미만 모델로 교체.
    현재는 구조 검증용 최소 구현.
    """

    def __init__(
        self,
        vocab_size: int,
        hidden_dim: int = 512,
        num_layers: int = 4,
        num_heads: int = 8,
        max_seq_len: int = 512,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.embedding = nn.Embedding(vocab_size, hidden_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim, nhead=num_heads, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.lm_head = nn.Linear(hidden_dim, vocab_size, bias=False)
        self.policy = PolicyEngine()

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        x = self.embedding(input_ids)
        x = self.transformer(x)
        return self.lm_head(x)  # (batch, seq_len, vocab)

    @torch.no_grad()
    def generate(self, input_ids: torch.Tensor, max_new_tokens: int = 64) -> dict:
        """
        Spirit Score 게이트 통과 후 생성.
        score < 0.75 이면 생성을 차단하고 이유를 반환.
        """
        logits = self.forward(input_ids)
        spirit_result = self.policy.evaluate(logits=logits.cpu())

        if not spirit_result["passed"]:
            return {
                "passed": False,
                "spirit_score": spirit_result["score"],
                "reason": spirit_result["reason"],
                "output_ids": None,
            }

        # greedy decoding
        generated = input_ids.clone()
        for _ in range(max_new_tokens):
            out = self.forward(generated)
            next_token = out[:, -1, :].argmax(dim=-1, keepdim=True)
            generated = torch.cat([generated, next_token], dim=1)
            if next_token.item() == 2:  # eos placeholder
                break

        return {
            "passed": True,
            "spirit_score": spirit_result["score"],
            "reason": "OK",
            "output_ids": generated,
        }

    def parameter_count(self) -> str:
        total = sum(p.numel() for p in self.parameters())
        return f"{total / 1e6:.1f}M"
