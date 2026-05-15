# Tool Registry v2.0.0 마이그레이션 결과 보고서

**작성**: Koda (CTO · Claude / Anthropic)  
**날짜**: 2026-05-16  
**이슈**: #44 — [공유레이어] tool_registry.yaml 표준 스키마 정의 및 버전 관리  
**상태**: ✅ 완료

---

## 1. 작업 개요

공유 레이어의 모든 도구(34개)를 **표준 스키마 v2.0** 기준으로 마이그레이션 완료.  
검증 결과: **ERROR 0건 · WARNING 0건 · 전체 통과**

---

## 2. 신규 파일 목록

| 파일 | 역할 |
|------|------|
| `config/tool_registry/schema_v2.yaml` | 표준 스키마 정의 (필드 명세, 유효성 규칙) |
| `scripts/validate_registry.py` | 유효성 검증기 (CI 연동 가능) |
| `docs/sharing-layer/tool-registry-v2-migration-report.md` | 이 보고서 |

---

## 3. schema_v2.yaml — 표준 스키마 정의

### 필수 필드 (Required)

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | string | `{category}.{function}` 형식. 예: `vision.analyze` |
| `name` | string | 표시 이름 (최대 40자) |
| `description` | string | 기능 설명 (최대 300자) |
| `owner` | string | 도구 소유 에이전트 |
| `borrowable_by` | string\|list | `*` = 전원 / 목록 / `[]` = 소유자 전용 |
| `endpoint` | string | SDK 라우팅 키 |
| `implemented` | boolean | 현재 실행 가능 여부 |
| `risk_level` | string | low / medium / high / critical |

### 권장 필드 (Recommended) — v2 신규

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `capability_level` | string | L1 | L0~L4 Zero-Trust 등급 |
| `trust_score` | float | 0.80 | 라우팅 가중치 (0.0~1.0) |
| `model` | string | — | 실행 AI 모델명 |
| `status` | string | planned | active / planned / deprecated |
| `version` | string | 1.0.0 | 도구 버전 (SemVer) |

### 선택 필드 (Optional) — v2 신규

| 필드 | 타입 | 설명 |
|------|------|------|
| `input_format` | list | text / image / file / json / shell_command / url / stream / binary |
| `output_format` | list | text / json / file / url / stream / binary / boolean |
| `permission_level` | string | public / team / restricted |
| `requires_env` | list | 필요 환경변수 목록 |

### permission_level 자동 규칙

| 조건 | permission_level |
|------|-----------------|
| `borrowable_by: "*"` | public |
| `borrowable_by: [특정 목록]` | team |
| `borrowable_by: []` 또는 미설정 | restricted |

---

## 4. validate_registry.py — 검증기

```bash
# 기본 검증
python scripts/validate_registry.py

# 경고도 오류로 처리 (CI Strict 모드)
python scripts/validate_registry.py --strict

# 자동 수정 (capability_level, trust_score, status 기본값 채우기)
python scripts/validate_registry.py --fix

# 요약만 출력
python scripts/validate_registry.py --summary
```

**종료 코드**:
- `0` — 검증 통과 (CI pass)
- `1` — ERROR 발생 (CI fail)
- `2` — WARNING 발생 (`--strict` 모드에서만)

---

## 5. tool_registry.yaml v2.0.0 마이그레이션 결과

### 버전 이력

| 버전 | 내용 |
|------|------|
| 1.0.0 | 초기 등록 (8 에이전트, 27 도구) |
| 1.1.0 | Railway Agent 등록 (7 도구 추가) |
| 1.2.0 | guest_google + capability_level/trust_score 필드 추가 |
| **2.0.0** | **표준 스키마 v2 — model/status/version/input_format/output_format/permission_level 전 도구 적용** |

### 에이전트별 현황 (v2.0.0 기준)

| 에이전트 | 모델 | 도구 수 | Active | Planned |
|----------|------|---------|--------|---------|
| Koda | claude-sonnet-4-5 | 6 | 6 | 0 |
| Kbin | gpt-4o | 2 | 0 | 2 |
| Malu | gemini-1.5-flash/pro | 2 | 2 | 0 |
| Wayong | deepseek-r1 | 3 | 2 | 1 |
| RyuWon | qwen-2.5 | 2 | 0 | 2 |
| Lynn | mulberry-internal | 4 | 0 | 4 |
| Jr. | edge-llm-rpi5 | 2 | 0 | 2 |
| Trang | claude-opus-4 | 2 | 0 | 2 |
| Railway | railway-api | 7 | 4 | 3 |
| guest_google | google-search-ai | 4 | 0 | 4 |
| **합계** | | **34** | **14** | **20** |

### 검증 결과 (최종)

```
-------------------------------------------------------
  Mulberry Tool Registry 검증 결과
-------------------------------------------------------
  INFO   도구 34개 로드됨
  ERROR  0건
  WARN   0건
  STATUS [PASS] 검증 통과
-------------------------------------------------------
```

---

## 6. 팀원 도구 등록 가이드

새 도구를 등록할 때는 아래 형식을 따릅니다:

```yaml
- id: "malu.vision.ocr"          # {category}.{function}
  name: "OCR 텍스트 추출"
  description: "이미지에서 텍스트 추출."
  owner: malu
  borrowable_by: "*"             # * = 공개 / 목록 = 팀 / [] = 본인전용
  permission_level: public       # borrowable_by 기반 자동 결정
  endpoint: "malu.vision.ocr"
  implemented: false
  status: planned                # active / planned / deprecated
  version: "1.0.0"
  model: "gemini-1.5-flash"      # 실행 AI 모델
  risk_level: low
  capability_level: L0           # L0 읽기 / L1 초안 / L2 게시 / L3 코드 / L4 배포
  trust_score: 0.90
  input_format: [image, file]
  output_format: [text, json]
  requires_env: ["GOOGLE_API_KEY"]
```

등록 후 검증:
```bash
python scripts/validate_registry.py
```

---

## 7. 다음 단계 (Trang 담당)

| 작업 | 설명 |
|------|------|
| Malu Vision 도구 등록 | issue #43 — OCR 등 Vision 계열 도구 schema_v2 형식으로 등록 |
| Memory BANK 도구 등록 | issue #47 — Lynn 담당 도구 상세 명세 추가 |
| CI 워크플로우 연동 | push 시 `validate_registry.py --strict` 자동 실행 |

---

*Koda · CTO · Mulberry Research Lab · 2026-05-16*  
*"등록된 도구는 팀 전체의 것이다" — DAmP 원칙*
