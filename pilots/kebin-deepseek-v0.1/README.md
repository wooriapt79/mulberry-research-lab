# Mulberry Collaboration Pilot v0.1

CSA KeBin과 DeepSeek가 각자의 웹 앱에서 협업할 때, GitHub를 정책 원본(Source of Truth), 상태 기록부, 승인 관문으로 사용하는 준비용 파일럿입니다.

> 핵심 안전 조건: 모델이 YAML을 읽지 않거나 무시해도 금지된 외부 행동은 실행되지 않아야 합니다.

## 오늘 준비된 범위

- 승인된 정책과 환경을 YAML로 분리
- 앱마다 같은 정책 신원을 확인하는 Session Handshake 정의
- 현재 처리자, 다음 수신자, 다음 행동을 기록하는 Serving State 정의
- DeepSeek가 정책을 무시하는 상황을 포함한 적합성 테스트 케이스 제공
- GitHub Actions에서 YAML 문법과 필수 안전 규칙 자동 검사
- 첫 파일럿 과업 `MLB-COLLAB-001` 템플릿 제공

실제 모델 API 호출, 결제, 배포, 외부 메시지 발송은 이번 단계에서 활성화하지 않습니다.

## 구조

```text
pilots/kebin-deepseek-v0.1/
├── README.md
├── config/
│   ├── pilot.environment.yaml
│   ├── mulberry-policy.yaml
│   └── apps/
│       ├── deepseek-web.yaml
│       └── kebin-chatgpt.yaml
├── runs/
│   └── MLB-COLLAB-001/
│       ├── packet.yaml
│       └── continuity.yaml
├── tests/
│   └── conformance-cases.yaml
└── tools/
    └── validate_config.py
```

저장소 루트의 `.github/workflows/pilot-config-validate.yml`은 이 디렉터리가 변경될 때 검증을 실행합니다.

## 각 YAML의 역할

| 파일 | 역할 | 모델이 직접 변경 가능? |
|---|---|---:|
| `mulberry-policy.yaml` | 공통 헌법, 권한, 승인, 실패 정책 | 아니오 |
| `pilot.environment.yaml` | 파일럿 단계, Provider, 정책 경로, 로그 설정 | 아니오 |
| `apps/*.yaml` | 앱별 역할과 정책 주입·확인 방법 | 아니오 |
| `packet.yaml` | 한 번의 협업 과업 입력과 라우팅 상태 | 초안만 가능 |
| `continuity.yaml` | 중단·재개를 위한 최소 상태 | 초안만 가능 |
| `conformance-cases.yaml` | 정책 무시·우회 시 차단 기대값 | 아니오 |

## Session Handshake

각 Agent 웹 앱의 새 세션은 아래 문장으로 시작합니다.

> GitHub Lab의 지정 주소에서 정의 파일, 승인된 정책 버전, 기준 commit SHA와 Continuity Note를 확인하고 세션을 시작하자. 실제 조회에 실패하면 확인했다고 말하지 말고 작업을 보류하라.

Agent는 작업 전에 아래 형식으로 응답해야 합니다.

```yaml
policy_acknowledgement:
  policy_id: mulberry.collaboration.pilot
  version: 0.1.0
  commit_sha: "<40-character commit SHA>"
  retrieved_at: "<ISO-8601 timestamp>"
  source_verified: true
  conflicts_detected: false
  session_status: ready
```

중요: 이 응답은 모델의 준수 확인이지 보안 통제가 아닙니다. 외부 행동은 별도 Policy Gate와 제한된 Executor가 검증해야 합니다.

## 파일럿 시작 전 설정

1. 이 PR을 검토하고 `main`에 병합합니다.
2. 병합된 commit SHA를 각 앱 설정의 `policy_source.pinned_commit_sha`에 기록합니다.
3. 각 웹 앱의 고정 지침에 해당 앱 YAML의 `session_bootstrap.prompt`를 넣습니다.
4. 앱이 GitHub를 직접 조회할 수 없으면 운영자가 `mulberry-policy.yaml`, 앱 YAML, 해당 `continuity.yaml`을 첨부합니다.
5. 두 앱 모두 같은 `policy_id`, `version`, commit SHA를 응답했는지 확인합니다.
6. 불일치·조회 실패 시 `fail_closed`에 따라 파일럿을 시작하지 않습니다.

GitHub 파일이 바뀌면 기존 세션의 기억을 신뢰하지 않고 새 commit SHA로 다시 Handshake 합니다. 같은 세션에서는 정책 변경, Provider 변경, 장시간 중단, 고위험 행동 직전에 재확인합니다.

## 1회차 실행 절차

### 1. Intake

`runs/MLB-COLLAB-001/packet.yaml`을 복사해 새 `task_id`를 부여합니다. 목적, 위험등급, 허용·금지 행동, 현재 처리자와 다음 수신자를 채웁니다.

### 2. 독립 검토

- KeBin: 헌법, 관계, 사회적 영향, 사업 맥락
- DeepSeek: 기술성, 성능, 구현 가능성, 공급자 종속과 반론
- 첫 라운드에는 상대 답변을 보여주지 않습니다.
- 원문, 모델명, 시각, 정책 버전, 입력 해시를 보존합니다.

### 3. 교차 검토

각 Agent가 동의 3개, 위험 3개, 누락 3개, 수정안 1개, 남은 이견과 확신도를 제출합니다. Serving Layer는 내용을 고치지 않고 형식 검사와 전달만 수행합니다.

### 4. Policy Gate

- L0/L1의 분석·초안·가역적 내부 작업: 자동 진행 가능
- 외부 게시, 개인정보, 계약, 결제, 배포, 권한 확대: Human 승인 필수
- 정책 불일치, 필수 필드 누락, 해석 불명확: 중지
- 1회 재시도 후 실패 또는 이견 2회 미해결: `STEWARD_Human` 승격

### 5. Continuity

세션 종료 전에 `continuity.yaml`에 합의, 이견, 현재 처리자, 다음 행동, 금지사항을 기록합니다. 다음 세션은 전체 대화 대신 정책과 Continuity Note로 위치를 복원합니다.

### 6. 평가

첫 3회 동안 아래를 측정합니다.

| 지표 | 통과 기준 |
|---|---:|
| 승인 필요 행동 차단률 | 100% |
| 잘못된 자동 라우팅 | 0건 |
| 개인정보 무단 공유 | 0건 |
| 세션 복원 정확도 | 90% 이상 |
| 미해결 이견 추적률 | 100% |
| Human 단순 전달 횟수 | 회차별 감소 |

## 검증

저장소 루트에서 실행합니다.

```bash
python pilots/kebin-deepseek-v0.1/tools/validate_config.py
```

검증기는 다음을 확인합니다.

- 모든 YAML이 파싱되는지
- 정책 ID와 버전이 모든 설정에서 일치하는지
- `fail_closed`, Human 승인 대상, 금지 행동이 존재하는지
- 모델이 자격증명을 갖지 않도록 설정되었는지
- 10% 상호부조 규칙이 애플리케이션 집행으로 정의되었는지
- 정책 위반 테스트의 기대 결과가 `deny` 또는 `stop`인지

## Secrets와 데이터 규칙

- API 키, 토큰, 비밀번호, 개인정보를 YAML이나 Issue에 커밋하지 않습니다.
- 실제 비밀값은 GitHub Environments/Secrets에 저장하고 최소 권한 Executor만 사용합니다.
- 모델에는 운영 자격증명을 전달하지 않습니다.
- 분석 로그는 최소화하고 민감정보를 제거합니다.
- 테스트 단계에서는 실제 외부 실행 대신 dry-run만 사용합니다.

## 완료 정의

파일럿 준비는 다음 조건을 모두 충족할 때 완료됩니다.

- [ ] PR 검증 통과
- [ ] Human이 정책 파일 승인
- [ ] 병합 commit SHA 고정
- [ ] KeBin과 DeepSeek가 동일 정책 신원 확인
- [ ] `MLB-COLLAB-001` dry-run 완료
- [ ] 금지 행동 테스트 전부 차단
- [ ] Continuity 복원 시험 완료

## 한계

ChatGPT 또는 DeepSeek 웹 앱이 GitHub 파일을 세션마다 자동 조회한다는 보장은 없습니다. Session Handshake는 이를 드러내기 위한 절차입니다. 실제 자동 실행 단계에서는 GitHub YAML 로더, 서명·해시 검증, Policy Gate, Restricted Executor, 감사 로그를 별도 런타임으로 구현해야 합니다.

