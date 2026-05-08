"""
Teacher Instruct — DeepSeek Coder 6.7b-instruct wrapper.

역할: 대화형 지식 교사. apply_chat_template()으로 질의응답 형태의
소프트 레이블(logit distribution)을 생성한다.
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from dataclasses import dataclass


@dataclass
class InstructOutput:
    logits: torch.Tensor        # (batch, seq_len, vocab)
    hidden_states: torch.Tensor # last encoder layer
    generated_text: str


class TeacherInstruct:
    MODEL_ID = "deepseek-ai/deepseek-coder-6.7b-instruct"

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
    def get_soft_labels(self, prompt: str, max_new_tokens: int = 256) -> InstructOutput:
        """
        Chat-template 기반 소프트 레이블 추출.
        생성된 토큰의 logit distribution을 반환한다.
        """
        messages = [{"role": "user", "content": prompt}]
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(self.device)

        outputs = self.model(
            inputs,
            output_hidden_states=True,
        )

        # 생성 텍스트 (디코딩 확인용)
        generated = self.model.generate(
            inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            top_k=50,
            top_p=0.95,
            num_return_sequences=1,
            eos_token_id=self.tokenizer.eos_token_id,
        )
        text = self.tokenizer.decode(
            generated[0][inputs.shape[1]:], skip_special_tokens=True
        )

        return InstructOutput(
            logits=outputs.logits,
            hidden_states=outputs.hidden_states[-1],
            generated_text=text,
        )

    def encode_batch(self, prompts: list[str]) -> list[InstructOutput]:
        return [self.get_soft_labels(p) for p in prompts]
