"""
Mulberry Tool Registry 유효성 검증기 — #44

표준 스키마 v2.0 기준으로 tool_registry.yaml을 검증한다.
GitHub Actions CI 및 로컬 push 전 실행 권장.

사용법:
  python scripts/validate_registry.py
  python scripts/validate_registry.py --strict    (경고도 오류로 처리)
  python scripts/validate_registry.py --fix       (자동 수정 가능한 항목 수정)
  python scripts/validate_registry.py --summary   (요약만 출력)

종료 코드:
  0  — 검증 통과
  1  — ERROR 발생 (CI에서 fail)
  2  — WARNING 발생 (--strict 시 fail)

설계: Koda (CTO) · #44 (2026-05-15)
"""

from __future__ import annotations

import argparse
import re
import sys
import io
from pathlib import Path
from typing import Any

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML 필요: pip install PyYAML")
    sys.exit(1)

# ── 경로 설정 ─────────────────────────────────────────────────────
ROOT          = Path(__file__).parent.parent
REGISTRY_PATH = ROOT / "mulberry_connector" / "tool_registry.yaml"
SCHEMA_PATH   = ROOT / "config" / "tool_registry" / "schema_v2.yaml"

# ── 상수 ──────────────────────────────────────────────────────────
VALID_OWNERS      = {"koda","kbin","malu","wayong","ryuwon","lynn","jr","trang","railway","guest_google"}
VALID_RISK        = {"low", "medium", "high", "critical"}
VALID_CAP         = {"L0", "L1", "L2", "L3", "L4"}
VALID_STATUS      = {"active", "planned", "deprecated"}
VALID_PERMISSION  = {"public", "team", "restricted"}
VALID_IN_FMT      = {"text","image","file","json","shell_command","url","stream","binary"}
VALID_OUT_FMT     = {"text","json","file","url","stream","binary","boolean"}
ID_PATTERN        = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_.]*$")
VERSION_PATTERN   = re.compile(r"^\d+\.\d+\.\d+$")


# ── 결과 수집 ─────────────────────────────────────────────────────
class ValidationResult:
    def __init__(self):
        self.errors:   list[str] = []
        self.warnings: list[str] = []
        self.infos:    list[str] = []
        self.fixed:    list[str] = []

    def error(self, msg: str):   self.errors.append(msg)
    def warning(self, msg: str): self.warnings.append(msg)
    def info(self, msg: str):    self.infos.append(msg)
    def fix(self, msg: str):     self.fixed.append(msg)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


# ── 개별 도구 검증 ────────────────────────────────────────────────

def validate_tool(tool: dict, result: ValidationResult, auto_fix: bool) -> dict:
    """단일 도구 항목 검증. auto_fix=True면 수정 가능한 항목 자동 보정."""
    tid = tool.get("id", "<unknown>")
    prefix = f"[{tid}]"

    # ── 필수 필드 ────────────────────────────────────────────────
    for field in ["id", "name", "description", "owner", "endpoint", "implemented", "risk_level"]:
        if field not in tool:
            result.error(f"{prefix} 필수 필드 누락: {field}")

    # id 형식 검증
    if "id" in tool:
        if not ID_PATTERN.match(str(tool["id"])):
            result.error(f"{prefix} id 형식 오류: '{tool['id']}' — 형식: category.function")

    # owner 유효성
    if "owner" in tool and tool["owner"] not in VALID_OWNERS:
        result.error(f"{prefix} 알 수 없는 owner: '{tool['owner']}'")

    # risk_level 유효성
    if "risk_level" in tool and tool["risk_level"] not in VALID_RISK:
        result.error(f"{prefix} 잘못된 risk_level: '{tool['risk_level']}'")

    # implemented 타입 체크
    if "implemented" in tool and not isinstance(tool["implemented"], bool):
        result.error(f"{prefix} implemented 는 boolean 이어야 합니다: {type(tool['implemented'])}")

    # ── 권장 필드 (없으면 경고) ──────────────────────────────────
    if "capability_level" not in tool:
        result.warning(f"{prefix} capability_level 미설정 (기본값 L1 권장)")
        if auto_fix:
            tool["capability_level"] = "L1"
            result.fix(f"{prefix} capability_level = L1 자동 설정")
    elif tool["capability_level"] not in VALID_CAP:
        result.error(f"{prefix} 잘못된 capability_level: '{tool['capability_level']}'")

    if "trust_score" not in tool:
        result.warning(f"{prefix} trust_score 미설정 (기본값 0.80 권장)")
        if auto_fix:
            tool["trust_score"] = 0.80
            result.fix(f"{prefix} trust_score = 0.80 자동 설정")
    else:
        ts = tool["trust_score"]
        if not isinstance(ts, (int, float)) or not (0.0 <= float(ts) <= 1.0):
            result.error(f"{prefix} trust_score 범위 오류: {ts} (0.0~1.0)")

    if "model" not in tool:
        result.warning(f"{prefix} model 미설정 (어떤 AI 모델인지 명시 권장)")

    if "status" not in tool:
        result.warning(f"{prefix} status 미설정")
        if auto_fix:
            # implemented 에서 자동 유추
            impl = tool.get("implemented", False)
            tool["status"] = "active" if impl else "planned"
            result.fix(f"{prefix} status = {'active' if impl else 'planned'} 자동 설정")
    elif tool["status"] not in VALID_STATUS:
        result.error(f"{prefix} 잘못된 status: '{tool['status']}'")

    # implemented 와 status 일관성 체크
    if "status" in tool and "implemented" in tool:
        impl    = tool["implemented"]
        status  = tool["status"]
        if impl and status == "planned":
            result.warning(f"{prefix} implemented=true 인데 status=planned — 불일치")
        if not impl and status == "active":
            result.warning(f"{prefix} implemented=false 인데 status=active — 불일치")

    if "version" in tool and not VERSION_PATTERN.match(str(tool["version"])):
        result.error(f"{prefix} version 형식 오류: '{tool['version']}' (SemVer: X.Y.Z)")

    # ── 선택 필드 검증 (있으면 형식 확인) ───────────────────────
    if "input_format" in tool:
        bad = [f for f in (tool["input_format"] or []) if f not in VALID_IN_FMT]
        if bad:
            result.error(f"{prefix} 알 수 없는 input_format: {bad}")

    if "output_format" in tool:
        bad = [f for f in (tool["output_format"] or []) if f not in VALID_OUT_FMT]
        if bad:
            result.error(f"{prefix} 알 수 없는 output_format: {bad}")

    if "permission_level" in tool and tool["permission_level"] not in VALID_PERMISSION:
        result.error(f"{prefix} 잘못된 permission_level: '{tool['permission_level']}'")

    # borrowable_by 와 permission_level 일관성
    if "borrowable_by" in tool and "permission_level" in tool:
        bb = tool["borrowable_by"]
        pl = tool["permission_level"]
        is_public = bb == "*" or bb == ["*"]
        if is_public and pl != "public":
            result.warning(f"{prefix} borrowable_by='*' 인데 permission_level='{pl}' — 'public' 권장")
        if isinstance(bb, list) and len(bb) > 0 and not is_public and pl == "public":
            result.warning(f"{prefix} borrowable_by=목록 인데 permission_level='public' — 'team' 권장")

    # ── 중복 endpoint 체크는 상위에서 처리 ──────────────────────
    return tool


# ── 메타 검증 ─────────────────────────────────────────────────────

def validate_meta(data: dict, tools: list[dict], result: ValidationResult):
    meta = data.get("meta", {})
    if not meta:
        result.warning("meta 섹션 없음")
        return

    # agents 수 체크
    owners = {t.get("owner") for t in tools if t.get("owner")}
    declared = meta.get("agents", 0)
    if declared != len(owners):
        result.warning(
            f"meta.agents={declared} 이나 실제 owner 수={len(owners)}: {sorted(owners)}"
        )

    # tools_total 체크
    declared_total = meta.get("tools_total", 0)
    if declared_total != len(tools):
        result.warning(
            f"meta.tools_total={declared_total} 이나 실제 도구 수={len(tools)}"
        )

    # 버전 형식
    version = meta.get("version", "")
    if version and not VERSION_PATTERN.match(str(version)):
        result.error(f"meta.version 형식 오류: '{version}'")


# ── 중복 id 검증 ──────────────────────────────────────────────────

def check_duplicates(tools: list[dict], result: ValidationResult):
    seen: dict[str, int] = {}
    for i, tool in enumerate(tools):
        tid = tool.get("id")
        if tid:
            if tid in seen:
                result.error(f"중복 id '{tid}': #{seen[tid]+1}번과 #{i+1}번")
            else:
                seen[tid] = i


# ── 메인 검증 함수 ────────────────────────────────────────────────

def validate(
    registry_path: Path = REGISTRY_PATH,
    auto_fix: bool = False,
) -> tuple[ValidationResult, dict]:

    result = ValidationResult()

    if not registry_path.exists():
        result.error(f"파일 없음: {registry_path}")
        return result, {}

    try:
        with open(registry_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        result.error(f"YAML 파싱 실패: {e}")
        return result, {}

    tools: list[dict] = data.get("tools", [])
    if not tools:
        result.error("tools 섹션이 비어 있거나 없음")
        return result, data

    result.info(f"도구 {len(tools)}개 로드됨")

    # 중복 체크
    check_duplicates(tools, result)

    # 개별 도구 검증
    fixed_tools = []
    for tool in tools:
        fixed = validate_tool(tool, result, auto_fix)
        fixed_tools.append(fixed)

    # 메타 검증
    validate_meta(data, tools, result)

    if auto_fix:
        data["tools"] = fixed_tools
        # meta 업데이트
        if "meta" in data:
            from datetime import date
            data["meta"]["updated"] = str(date.today())

    return result, data


# ── 출력 ──────────────────────────────────────────────────────────

def print_report(result: ValidationResult, summary_only: bool = False):
    SEP = "-" * 55

    if not summary_only:
        if result.errors:
            print(f"\n[ERROR] {len(result.errors)}건")
            for e in result.errors:
                print(f"  ERROR  {e}")

        if result.warnings:
            print(f"\n[WARN] {len(result.warnings)}건")
            for w in result.warnings:
                print(f"  WARN   {w}")

        if result.fixed:
            print(f"\n[FIX] {len(result.fixed)}건 자동 수정")
            for f in result.fixed:
                print(f"  FIX    {f}")

    print(f"\n{SEP}")
    print(f"  Mulberry Tool Registry 검증 결과")
    print(SEP)
    for i in result.infos:
        print(f"  INFO   {i}")
    print(f"  ERROR  {len(result.errors)}건")
    print(f"  WARN   {len(result.warnings)}건")
    if result.fixed:
        print(f"  FIX    {len(result.fixed)}건 자동 수정")

    if result.ok:
        print(f"  STATUS [PASS] 검증 통과")
    else:
        print(f"  STATUS [FAIL] 오류 수정 필요")
    print(SEP)


# ── 진입점 ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Mulberry Tool Registry 유효성 검증기")
    parser.add_argument("--strict",  action="store_true", help="경고도 오류로 처리")
    parser.add_argument("--fix",     action="store_true", help="자동 수정 가능한 항목 수정 후 저장")
    parser.add_argument("--summary", action="store_true", help="요약만 출력")
    parser.add_argument("--file",    type=str, default=str(REGISTRY_PATH), help="검증할 YAML 파일 경로")
    args = parser.parse_args()

    registry_path = Path(args.file)
    result, data  = validate(registry_path, auto_fix=args.fix)

    print_report(result, summary_only=args.summary)

    # --fix: 수정된 내용 저장
    if args.fix and result.fixed and data:
        with open(registry_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"\n  저장 완료: {registry_path}")

    # 종료 코드
    if result.errors:
        sys.exit(1)
    if args.strict and result.warnings:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
