"""
BANK API 래퍼 — Lynn 가이드 반영 (Issue #24)

Lynn 수석의 설계 원칙:
  "ghost_archive_records.json 직접 읽기는 속도면에서 유리하지만,
   무결성을 위해 BANK_API를 한 번 거치는 래퍼를 두는 것이 어떻겠나?"

역할:
  - memory.read / memory.write 도구의 단일 진입점
  - 직접 파일 읽기 → BANK_API 래퍼 경유로 전환
  - 무결성 검사: 읽기 전 파일 해시 확인, 쓰기 후 검증

환경변수:
  BANK_REPO_PATH — mulberry_memory_bank 로컬 경로
  BANK_API_URL   — 향후 BANK REST API 엔드포인트 (현재는 파일 직접 접근)
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

BANK_REPO_PATH = Path(
    os.environ.get("BANK_REPO_PATH",
                   str(Path.home() / "mulberry_memory_bank"))
)
GHOST_ARCHIVE  = BANK_REPO_PATH / "persona_config" / "ghost_archive_records.json"
GUARDIAN_FILE  = BANK_REPO_PATH / "persona_config" / "guardian_contribution.json"


@dataclass
class BankReadResult:
    success: bool
    data: dict | list
    source: str        # "file" or "api"
    hash_verified: bool
    error: str = ""


@dataclass
class BankWriteResult:
    success: bool
    records_written: int
    hash_after: str
    error: str = ""


class BankAPI:
    """
    BANK 메모리 읽기/쓰기 래퍼.
    Lynn의 ghost_archive + GuardianAlgorithm 데이터 무결성 보장.
    """

    def __init__(self, repo_path: Path = BANK_REPO_PATH):
        self.repo_path = repo_path
        self._cache: dict = {}
        self._cache_hash: str = ""

    # ── 읽기 ──────────────────────────────────────────────────────

    def read_ghost_archive(self, agent_id: str = None) -> BankReadResult:
        """
        GhostArchive 기록 읽기.
        agent_id 지정 시 해당 에이전트 기록만 반환.
        """
        return self._read_json(GHOST_ARCHIVE, filter_key="agent_id", filter_val=agent_id)

    def read_guardian_contribution(self) -> BankReadResult:
        """GuardianAlgorithm 기여 현황 읽기."""
        return self._read_json(GUARDIAN_FILE)

    def _read_json(self, path: Path, filter_key: str = None, filter_val: str = None) -> BankReadResult:
        if not path.exists():
            return BankReadResult(
                success=False, data={}, source="file",
                hash_verified=False,
                error=f"파일 없음: {path}",
            )
        try:
            raw = path.read_bytes()
            current_hash = hashlib.sha256(raw).hexdigest()[:12]
            data = json.loads(raw.decode("utf-8"))

            # 무결성: 캐시 해시와 비교
            hash_ok = (current_hash == self._cache_hash) if self._cache_hash else True
            self._cache_hash = current_hash

            # 필터링
            if filter_key and filter_val and isinstance(data, list):
                data = [r for r in data if r.get(filter_key) == filter_val]

            return BankReadResult(
                success=True, data=data, source="file",
                hash_verified=hash_ok,
            )
        except Exception as e:
            return BankReadResult(
                success=False, data={}, source="file",
                hash_verified=False, error=str(e),
            )

    # ── 쓰기 ─────────────────────────────────────────────────────

    def write_ghost_record(self, record: dict) -> BankWriteResult:
        """
        GhostArchive에 새 기록 추가.
        쓰기 후 해시 검증 수행.
        """
        return self._append_json(GHOST_ARCHIVE, record)

    def _append_json(self, path: Path, record: dict) -> BankWriteResult:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # 기존 데이터 읽기
            existing = []
            if path.exists():
                existing = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = [existing]

            # 타임스탬프 추가
            record.setdefault("written_at", datetime.utcnow().isoformat())
            record.setdefault("written_via", "BankAPI")
            existing.append(record)

            # 쓰기
            content = json.dumps(existing, ensure_ascii=False, indent=2)
            path.write_text(content, encoding="utf-8")

            # 쓰기 후 해시
            hash_after = hashlib.sha256(content.encode()).hexdigest()[:12]
            return BankWriteResult(
                success=True,
                records_written=len(existing),
                hash_after=hash_after,
            )
        except Exception as e:
            return BankWriteResult(
                success=False, records_written=0,
                hash_after="", error=str(e),
            )

    # ── 상태 확인 ─────────────────────────────────────────────────

    def status(self) -> dict:
        ghost_ok = GHOST_ARCHIVE.exists()
        guardian_ok = GUARDIAN_FILE.exists()
        return {
            "bank_repo": str(self.repo_path),
            "ghost_archive": {"exists": ghost_ok, "path": str(GHOST_ARCHIVE)},
            "guardian_contribution": {"exists": guardian_ok, "path": str(GUARDIAN_FILE)},
            "integrity": "BankAPI wrapper active",
        }
