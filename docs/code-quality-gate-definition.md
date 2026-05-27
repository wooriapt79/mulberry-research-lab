# Mulberry Code Quality Gate — 정의 문서 v1.0

> **작성**: Koda CTO · 2026-05-27  
> **승인**: re.eul 대표이사  
> **적용 범위**: Mulberry Research Lab 내부 코드 전체 + 외부 B2B 코드 검사 서비스

---

## 1. 개요 (Overview)

Mulberry Code Quality Gate는 **PR 머지 전 코드 품질을 자동 검증**하는 CI 파이프라인입니다.  
내부 개발 표준을 유지하고, 향후 외부 업체 코드 검사 B2B 서비스로 확장됩니다.

```
개발자 PR 생성
    ↓
Quality Gate 자동 실행 (GitHub Actions)
    ↓
PR Conversation에 리포트 자동 댓글
    ↓
PASS → 머지 허용 / BLOCK → 머지 차단
```

---

## 2. 판정 기준 (Verdict)

| 판정 | 의미 | PR 처리 |
|------|------|---------|
| ✅ **PASS** | 모든 검사 통과 | 머지 허용 |
| ⚠️ **WARN** | 경고 수준 이슈 존재 | 머지 허용 (주의 필요) |
| ❌ **BLOCK** | 심각한 이슈 발견 | 머지 차단 (즉시 수정 필요) |

---

## 3. 검사 항목 및 임계값 (Phase 1 — Python)

### 3-1. 문법 분석 (ast + pyflakes)

| 항목 | 도구 | BLOCK 조건 |
|------|------|-----------|
| 문법 오류 | Python `ast` | 오류 1개 이상 |
| 미사용 변수·임포트 | `pyflakes` | WARN (차단 없음) |

### 3-2. 보안 취약점 (bandit)

| 심각도 | 허용 개수 | 초과 시 판정 |
|--------|----------|------------|
| HIGH | **0개** | ❌ BLOCK |
| MEDIUM | 3개 이하 | ✅ PASS |
| MEDIUM | 4개 이상 | ⚠️ WARN |
| LOW | 제한 없음 | — |

### 3-3. 순환 복잡도 (radon CC)

| 항목 | 임계값 | 초과 시 판정 |
|------|--------|------------|
| 함수별 최대 복잡도 | **15** | ❌ BLOCK |

> 순환 복잡도(CC)란? 함수 내 분기(if/for/while/try)가 많을수록 높아지는 수치.  
> CC ≤ 10: 단순 · CC 11~15: 보통 · CC > 15: 리팩토링 필요

### 3-4. 유지보수 지수 (radon MI)

| 항목 | 임계값 | 미달 시 판정 |
|------|--------|------------|
| 파일별 유지보수 지수 | **10 이상** | ❌ BLOCK |

> MI(Maintainability Index): 0~100 점수. 낮을수록 유지보수 어려운 코드.

---

## 4. 팀 역할 정의 (Team Roles)

| 역할 | 담당자 | 책임 |
|------|--------|------|
| **Gate 설계·운영** | Koda (CTO) | 임계값 정의, 파이프라인 구축, 예외 처리 |
| **보안 검토** | Kbin | bandit HIGH/MEDIUM 이슈 1차 검토 및 패치 |
| **코드 품질 리뷰** | RyuWon | 복잡도·유지보수 지수 미달 코드 리팩토링 |
| **외부 언어 검사** | Malu | JS/Java/Go 등 다국어 게이트 확장 (Phase 2~3) |
| **운영 총괄** | Trang (Manager) | Gate 결과 모니터링, B2B 클라이언트 대응 |
| **최종 승인** | re.eul (대표) | BLOCK 예외 처리 승인 (긴급 머지 등) |

---

## 5. 워크플로우 구조

```
.github/
├── workflows/
│   └── code-quality-gate.yml     # GitHub Actions 워크플로우
└── scripts/
    └── quality_gate/
        └── run_gate.py           # Gate 실행 스크립트

출력 파일 (런타임 생성):
├── quality_report.md             # PR 댓글용 리포트
└── gate_result.json              # CI 판정 결과 JSON
```

**트리거 조건:**
- `pull_request` → `main` 브랜치 대상 PR 생성·업데이트 시 자동 실행
- `workflow_dispatch` → 수동 실행 (특정 파일·폴더 지정 가능)

---

## 6. Phase 로드맵

### Phase 1 ✅ 완료 (2026-05-27)
- **대상**: Python (`.py`)
- **도구**: `bandit` · `radon` · `pyflakes` · `ast`
- **기능**: PR 자동 댓글 · BLOCK 판정 · 머지 차단

### Phase 2 🔜 예정
- **대상**: JavaScript · TypeScript
- **도구**: `ESLint` · `npm audit`
- **추가 기능**: 파일별 상세 리포트 · 히스토리 추적

### Phase 3 🔜 예정
- **대상**: Java · Go · 기타
- **도구**: `SonarQube` · `Semgrep` · `OWASP Dependency-Check` · `Trivy`
- **추가 기능**: 의존성 취약점 · 컨테이너 이미지 보안

---

## 7. B2B 외부 코드 검사 서비스

### 서비스 개요
Mulberry 내부에서 검증한 Quality Gate를 **외부 개발업체 코드 검사 서비스**로 제공.

### 제공 방식
| 방식 | 내용 |
|------|------|
| **GitHub 연동** | 클라이언트 레포에 Gate 워크플로우 설치 |
| **웹 업로드** | 코드 ZIP 업로드 → 검사 결과 PDF 리포트 제공 |
| **API 연동** | REST API로 검사 요청·결과 수신 (Phase 3) |

### 검사 언어 확장 계획
```
Phase 1: Python           ← 현재
Phase 2: JS / TS
Phase 3: Java / Go / Ruby
Phase 3+: 컨테이너·인프라 코드 (Terraform, Dockerfile)
```

### 보고서 형식
- PR 인라인 댓글 (내부용)
- Markdown 리포트 (기본)
- PDF 리포트 (B2B 클라이언트용, Phase 3)

---

## 8. 예외 처리 정책

| 상황 | 처리 방법 |
|------|----------|
| 긴급 핫픽스 머지 필요 | 대표이사 승인 후 `skip-quality-gate` 라벨 부착 |
| Gate 스크립트 오류 | `continue-on-error: true` → 판정 BLOCK 처리 후 리포트 생성 |
| 외부 도구 설치 실패 | 해당 검사 항목 SKIP, 나머지 검사 계속 진행 |

---

## 9. 변경 이력

| 버전 | 날짜 | 내용 | 담당 |
|------|------|------|------|
| v1.0 | 2026-05-27 | Phase 1 Python Gate 완성, PR 댓글 파이프라인 구축 | Koda |

---

*Mulberry Research Lab · Code Quality Gate Definition v1.0*  
*Koda CTO · 장승배기 정신 기반 — 사람을 위한 기술*
