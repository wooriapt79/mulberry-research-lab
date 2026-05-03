
# src/persona/base_persona_adapter.py
from abc import ABC, abstractmethod
from typing import Dict, Optional

class BasePersonaAdapter(ABC):
    """
    외부 페르소나 데이터를 Mulberry 참고자료로 변환하기 위한
    기본 어댑터 인터페이스 (추상 클래스).
    """
    @abstractmethod
    def adapt_reference(self, external_persona: Dict, source_note: str) -> Optional[Dict]:
        """
        외부 페르소나 데이터를 Mulberry 참고자료 형식으로 변환합니다.
        구체적인 구현은 각 데이터 소스별 어댑터에서 담당합니다.

        Args:
            external_persona (Dict): 변환할 외부 페르소나 데이터.
            source_note (str): 데이터 소스에 대한 설명.

        Returns:
            Optional[Dict]: Mulberry 형식의 페르소나 참고자료, 또는 검증 실패 시 None.
        """
