
# src/dialect/nemotron_adapter.py (개념안)
class NemotronPersonaAdapter:
    """
    Nemotron-Personas-Korea 데이터를 Mulberry 형식으로 변환
    """
    def map_to_mulberry_format(self, persona_record: dict) -> dict:
        return {
            "user_profile": {
                "age_group": persona_record.get("age"),
                "region": persona_record.get("region", "inje_gun"),
                "dialect_preference": persona_record.get("dialect", False),
                "vulnerability_flags": self._extract_vulnerability(persona_record)
            },
            "dialogue_pairs": [
                {
                    "input": turn["user"],
                    "expected_output": turn["assistant"],
                    "spirit_score": self._estimate_spirit(turn),
                    "task_type": self._classify_task(turn)
                }
                for turn in persona_record.get("dialogues", [])
            ]
        }
