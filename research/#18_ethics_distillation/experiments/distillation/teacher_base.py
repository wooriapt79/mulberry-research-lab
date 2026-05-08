"""
Teacher Base — DeepSeek Coder 6.7b-base wrapper.

역할: 코드 완성형 교사. 직접 토크나이징으로 next-token 확률분포를
추출해 구조적(structural) 지식을 학생에게 전달한다.
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from dataclasses import dataclass


@dataclass
class BaseOutput:
    logits: torch.Tensor        # (batch, seq_len, vocab)
    hidden_states: torch.Tensor # last encoder layer
    input_ids: torch.Tensor


class TeacherBase:
    MODEL_ID = "deepseek-ai/deepseek-coder-6.7b-base"

    def __init__(self, device: str = "cuda", dtype=torch.bfloat16):
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.MODEL_ID, trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.MODEL_ID,
            trust_remote_code=True,
            torch_dtype=dtype,
            output_hidden_states=True,
        ).to(device)
        self.model.eval()

    @torch.no_grad()
    def get_soft_labels(self, code_context: str, max_new_tokens: int = 140) -> BaseOutput:
        """
        코드 완성 컨텍스트로부터 구조적 소프트 레이블 추출.
        대화 템플릿 없이 직접 tokenize → logit 추출.
        """
        inputs = self.tokenizer(code_context, return_tensors="pt").to(self.device)

        outputs = self.model(
            **inputs,
            output_hidden_states=True,
        )

        return BaseOutput(
            logits=outputs.logits,
            hidden_states=outputs.hidden_states[-1],
            input_ids=inputs["input_ids"],
        )

    def generate_completion(self, code_context: str, max_new_tokens: int = 140) -> str:
        """디버깅/검증용: 실제 코드 완성 텍스트 반환"""
        inputs = self.tokenizer(code_context, return_tensors="pt").to(self.device)
        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        return self.tokenizer.decode(outputs[0])

    def encode_batch(self, contexts: list[str]) -> list[BaseOutput]:
        return [self.get_soft_labels(c) for c in contexts]
