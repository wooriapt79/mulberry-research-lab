# 🚀 Jr. TRANG 자율 성장 시스템 아키텍처

**작성일**: 2026-06-23  
**대상**: Jr. TRANG (Haiku 4.5 + 자동화 시스템)  
**정의자**: CEO re.eul  
**상태**: ✅ 실행 준비 완료

---

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [자동화 흐름도](#자동화-흐름도)
3. [GitHub 저장소 구조](#github-저장소-구조)
4. [워크플로우 실행 일정](#워크플로우-실행-일정)
5. [데이터 흐름](#데이터-흐름)
6. [필수 설정](#필수-설정)
7. [실행 로드맵](#실행-로드맵)

---

## 시스템 개요

### 핵심 개념

```
Jr. TRANG = Haiku 4.5 모델 + GitHub Actions + 외부 메모리 + 자동화

매주 반복되는 자율 성장 사이클:
  월요일 → 자가진단 (Self-Diagnosis)
  수요일 → 로직설계 (Design)
  금요일 → 자가개발 (Development)
  일요일 → 통합보고 (Integration & Report)

결과: 완전 자율적 Mythos AI로의 수렴
```

### 아키텍처 레이어

```
【Layer 1: 실행 엔진】
└─ GitHub Actions (Trigger & Orchestration)

【Layer 2: 로직 처리】
└─ Python Scripts
   ├─ JrTrangGrowthEngine.py (핵심 엔진)
   ├─ SelfAnalysisCode.py (자가진단)
   └─ SelfCodeGenerator.py (자동 코드 생성)

【Layer 3: 데이터 저장】
├─ AWS S3 (세션 메모리)
├─ BigQuery (메트릭 저장소)
└─ PostgreSQL (관계 DB)

【Layer 4: 시각화 & 리포팅】
├─ Data Studio (실시간 대시보드)
├─ GitHub Pages (공개 보고)
└─ Markdown (History.md)

【Layer 5: 협력 인터페이스】
├─ GitHub Issues (자가진단 결과)
├─ Pull Requests (코드 리뷰)
└─ Slack (알림)
```

---

## 자동화 흐름도

### 주간 자율 성장 사이클

```
┌─────────────────────────────────────────────────────────┐
│  【WEEK START】대표님의 "콜(노크)"                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  【월요일 09:00】 Step 1: 자가진단 (Self-Diagnosis)     │
│  ────────────────────────────────────────────────────────│
│  • JrTrangGrowthEngine 초기화                            │
│  • 지난주 메트릭 로드 (AWS S3)                          │
│  • 성능 분석 (10개 메트릭)                              │
│  • 병목 지점 식별 (Top 3)                               │
│  • 자가진단 리포트 생성                                 │
│  • GitHub Issues 자동 등록                              │
│  ────────────────────────────────────────────────────────│
│  출력: diagnosis_report.json                             │
│  저장: weekly_reports/week_XX.json                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  【수요일 14:00】 Step 2: 로직 설계 (Design Phase)     │
│  ────────────────────────────────────────────────────────│
│  • 자가진단 결과 분석                                   │
│  • 부족점별 개선 방안 설계                              │
│  • 구현 계획 자동 생성                                  │
│  • 코드 스켈레톤 작성                                   │
│  • 설계 문서화                                          │
│  ────────────────────────────────────────────────────────│
│  출력: design_report.json                                │
│  저장: design_specs/week_XX_design.md                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  【금요일 16:00】 Step 3: 자가 개발 (Development)      │
│  ────────────────────────────────────────────────────────│
│  • 설계 기반 코드 자동 생성                             │
│  • Unit Test 자동 작성                                  │
│  • 통합 테스트 실행                                     │
│  • 성능 벤치마크                                        │
│  • 개선된 코드 자동 커밋                                │
│  • Pull Request 자동 생성                               │
│  ────────────────────────────────────────────────────────│
│  출력: improved_code.py + tests/                         │
│  PR 제목: "🤖 Jr. TRANG Week XX Self-Development"       │
│  목표: Sr. TRANG 리뷰 대기                              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  【일요일 20:00】 Step 4: 통합 & 리포팅 (Integration)  │
│  ────────────────────────────────────────────────────────│
│  • PR 승인 여부 확인                                    │
│  • 주간 성과 검증                                       │
│  • 메트릭 최종 계산                                     │
│  • BigQuery 업로드                                      │
│  • Data Studio 대시보드 갱신                            │
│  • History.md 자동 기록                                 │
│  • 최종 커밋                                            │
│  ────────────────────────────────────────────────────────│
│  출력: verification_report.json                          │
│  저장: History.md (누적 기록)                            │
└─────────────────────────────────────────────────────────┘
                          ↓
        【WEEK END】다음주 월요일로 자동 반복
                          ↓
                  무한 성장 루프 (∞)
```

---

## GitHub 저장소 구조

### 메인 저장소: `mulberry-research-lab/jr-trang-self-improvement`

```
jr-trang-self-improvement/
│
├── 📂 src/                          # 핵심 엔진 (Python)
│   ├── JrTrangGrowthEngine.py       # 메인 성장 엔진
│   ├── SelfAnalysisCode.py          # 자가진단 로직
│   ├── SelfCodeGenerator.py         # 자동 코드 생성
│   └── TokenizerManager.py          # 토크나이저 관리
│
├── 📂 .github/workflows/             # GitHub Actions
│   ├── monday-self-diagnosis.yml    # Step 1: 월요일 자가진단
│   ├── wednesday-design.yml         # Step 2: 수요일 설계
│   ├── friday-development.yml       # Step 3: 금요일 개발
│   └── sunday-integration.yml       # Step 4: 일요일 통합
│
├── 📂 scripts/                       # 유틸리티 스크립트
│   ├── create_design_issues.py      # Design을 Issues로 변환
│   ├── update_dashboard.py          # Data Studio 갱신
│   ├── append_to_history.py         # History.md 기록
│   ├── performance_benchmark.py     # 성능 측정
│   └── deploy_to_railway.py         # Railway 배포
│
├── 📂 weekly_reports/                # 주간 진단 리포트
│   ├── week_01.json
│   ├── week_02.json
│   └── ...
│
├── 📂 design_specs/                  # 설계 문서
│   ├── week_01_design.md
│   ├── week_02_design.md
│   └── ...
│
├── 📂 tests/                         # 자동 테스트
│   ├── test_growth_engine.py
│   ├── test_self_analysis.py
│   └── test_code_generator.py
│
├── 📂 dashboards/                    # 대시보드 템플릿
│   ├── mythos_ai_dashboard.json
│   └── growth_metrics.html
│
├── 📂 docs/                          # 문서
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   └── FAQ.md
│
├── 📄 requirements.txt               # Python 의존성
├── 📄 .env.example                   # 환경변수 템플릿
├── 📄 README.md                      # 프로젝트 개요
└── 📄 History.md                     # 공식 성장 기록 (Sr. TRANG 기록)
```

### 서브 저장소 구조 (mulberry-research-lab 내)

```
mulberry-research-lab/
│
├── 【메인】 jr-trang-self-improvement/
│   └─ 자율 성장 엔진 + Workflows + 데이터
│
├── 【지원】 jr-trang-growth-engine/
│   ├─ Core Engine 소스
│   ├─ Unit Tests
│   └─ Performance Benchmarks
│
├── 【시각화】 jr-trang-dashboards/
│   ├─ Data Studio JSON
│   ├─ HTML Dashboards
│   └─ Chart Templates
│
├── 【자동화】 jr-trang-workflows/
│   ├─ Reusable Actions
│   ├─ Workflow Templates
│   └─ CI/CD Pipelines
│
└── 【문서】 jr-trang-documentation/
    ├─ Architecture Docs
    ├─ Setup Guides
    ├─ API References
    └─ Case Studies
```

---

## 워크플로우 실행 일정

### 자동 스케줄 (Weekly Cron)

```
시간대는 한국 시간(KST, UTC+9)

【매주 월요일 09:00】
Action: monday-self-diagnosis.yml
Trigger: 0 0 * * 1 (UTC)
내용: 자가진단 실행 → Issues 생성

【매주 수요일 14:00】
Action: wednesday-design.yml
Trigger: 0 5 * * 3 (UTC)
내용: 로직 설계 → 문서 생성

【매주 금요일 16:00】
Action: friday-development.yml
Trigger: 0 7 * * 5 (UTC)
내용: 코드 생성 → PR 생성

【매주 일요일 20:00】
Action: sunday-integration.yml
Trigger: 0 11 * * 0 (UTC)
내용: 통합 검증 → 최종 커밋
```

### 수동 트리거 옵션

```yaml
# 대표님이 필요시 언제든 실행 가능
on:
  workflow_dispatch:
    inputs:
      mode:
        description: 'Execution mode'
        required: true
        default: 'diagnosis'
        type: choice
        options:
          - diagnosis
          - design
          - development
          - integration
```

---

## 데이터 흐름

### End-to-End 데이터 파이프라인

```
【Step 1: 데이터 수집】
GitHub Actions (Monday)
     ↓
S3에서 이전 데이터 로드
BigQuery에서 메트릭 조회
     ↓

【Step 2: 분석】
JrTrangGrowthEngine 실행
메트릭 계산 (10개 항목)
병목 식별 (Top 3)
     ↓

【Step 3: 저장】
weekly_reports/week_XX.json (로컬)
AWS S3 백업
BigQuery 업로드
     ↓

【Step 4: 시각화】
Data Studio 자동 갱신
Growth Curve 업데이트
대시보드 공개
     ↓

【Step 5: 리포팅】
GitHub Pages에 공개
History.md 기록
Sr. TRANG에게 알림
     ↓

【다음 주】
동일 사이클 반복
```

### 데이터 저장소 (3단계)

```
【Tier 1: 핫 스토리지 (Hot)】
GitHub Repository (최신 1주)
└─ weekly_reports/ (JSON)

【Tier 2: 따뜻한 스토리지 (Warm)】
AWS S3 (최근 1개월)
└─ s3://jr-trang-metrics/weekly/

【Tier 3: 콜드 스토리지 (Cold)】
BigQuery (전체 히스토리)
└─ mulberry.jr_trang_metrics
```

---

## 필수 설정

### 1️⃣ GitHub Secrets 등록

**저장소 Settings → Secrets and variables**

```
필수 Secrets:
├─ AWS_ACCESS_KEY_ID
├─ AWS_SECRET_ACCESS_KEY
├─ BIGQUERY_PROJECT_ID
├─ BIGQUERY_CREDENTIALS (JSON 파일)
├─ SLACK_WEBHOOK_URL (선택)
└─ GITHUB_TOKEN (자동)
```

### 2️⃣ GitHub Actions 활성화

```
Settings → Actions → General
✅ Allow all actions and reusable workflows
✅ Allow actions created by GitHub
✅ Allow third-party actions
```

### 3️⃣ 환경 변수 파일 (.env)

```bash
# .env.example → .env로 복사 후 작성
AWS_REGION=ap-northeast-2
BIGQUERY_PROJECT=mulberry-ai
BIGQUERY_DATASET=jr_trang_metrics

S3_BUCKET=jr-trang-self-improvement
S3_PREFIX=metrics/

DATA_STUDIO_URL=https://...

GITHUB_REPO=mulberry-research-lab/jr-trang-self-improvement
GITHUB_BRANCH=main
```

### 4️⃣ Python 의존성

```bash
# requirements.txt
pandas==2.0.0
boto3==1.26.0
google-cloud-bigquery==3.10.0
google-cloud-storage==2.10.0
pydantic==2.0.0
requests==2.31.0
python-dotenv==1.0.0
pytest==7.3.0
pytest-cov==4.1.0
```

---

## 실행 로드맵

### Phase 1: 기초 구축 (Week 1-2)

```
【Week 1】
- [ ] GitHub 저장소 생성
- [ ] 디렉토리 구조 생성
- [ ] Workflows 기본 파일 작성
- [ ] Secrets 등록

【Week 2】
- [ ] Python 스크립트 작성
  └─ JrTrangGrowthEngine.py
  └─ SelfAnalysisCode.py
  └─ SelfCodeGenerator.py
- [ ] 의존성 설치 및 테스트
- [ ] 로컬 실행 확인
```

### Phase 2: 자동화 활성화 (Week 3-4)

```
【Week 3】
- [ ] GitHub Actions YAML 파일 업로드
- [ ] 각 Workflow 개별 테스트
  └─ monday-self-diagnosis.yml
  └─ wednesday-design.yml
  └─ friday-development.yml
  └─ sunday-integration.yml
- [ ] 오류 수정 및 최적화

【Week 4】
- [ ] 첫 주간 자동 실행
- [ ] 결과 검증
- [ ] Sr. TRANG 리뷰
- [ ] 완전 자동화 진입
```

### Phase 3: 최적화 (Week 5+)

```
【지속적 개선】
- [ ] 성능 최적화
- [ ] 오류 처리 강화
- [ ] 대시보드 고도화
- [ ] 팀 협력 강화
```

---

## 실행 명령어 (로컬 테스트)

### 로컬에서 Workflow 시뮬레이션

```bash
# 자가진단 실행
python src/JrTrangGrowthEngine.py --mode=diagnosis

# 설계 실행
python src/SelfAnalysisCode.py --mode=design

# 코드 생성 실행
python src/SelfCodeGenerator.py --design design_report.json

# 검증 실행
python src/JrTrangGrowthEngine.py --mode=verification

# 전체 테스트
pytest tests/ -v --cov=src/
```

### GitHub Actions 수동 트리거

```bash
# GitHub CLI 사용
gh workflow run monday-self-diagnosis.yml

# 또는 GitHub UI에서
Actions → Select Workflow → Run workflow
```

---

## 모니터링 & 알림

### 자동 알림 채널

```
【GitHub】
- Issues: 주간 자가진단 결과
- Pull Requests: 코드 개선 요청
- Discussions: 성장 과정 공유

【Slack (선택)】
- monday-diagnosis-channel
- friday-development-channel
- sunday-report-channel

【Email】
- Sr. TRANG에게 주간 요약 발송
- 비정상 발생시 즉시 알림
```

---

## 보안 & 프라이버시

### 민감 정보 보호

```
✅ GitHub Secrets에 API Key 저장
✅ .env 파일 .gitignore에 등록
✅ AWS IAM Role 최소 권한 원칙
✅ BigQuery 데이터 암호화
✅ 로그 자동 삭제 (30일)
```

---

## 트러블슈팅

### 일반적인 문제 & 해결책

```
【문제】Workflow가 실행되지 않음
해결: Settings → Actions → Workflows 활성화 확인

【문제】AWS 권한 오류
해결: IAM 정책 확인, AWS_SECRET_ACCESS_KEY 갱신

【문제】BigQuery 연결 실패
해결: BIGQUERY_CREDENTIALS JSON 파일 확인

【문제】GitHub Actions 타임아웃
해결: 스크립트 최적화, 병렬 실행 고려
```

---

## 성공 기준

### 자동화 완성도

```
✅ 월요일 09:00 → 자가진단 자동 실행
✅ 수요일 14:00 → 로직 설계 자동 실행
✅ 금요일 16:00 → 코드 생성 자동 실행
✅ 일요일 20:00 → 통합 리포팅 자동 실행

✅ GitHub에 자동 커밋
✅ BigQuery에 자동 저장
✅ Data Studio 자동 갱신
✅ Sr. TRANG에게 자동 알림

→ 완전 자율적 Mythos AI 구현
```

---

## 다음 단계

### 즉시 실행 (Week 1)

1. GitHub 저장소 생성
   ```
   https://github.com/mulberry-research-lab/jr-trang-self-improvement
   ```

2. 저장소 클론 및 초기 설정
   ```bash
   git clone [위 URL]
   cd jr-trang-self-improvement
   mkdir -p src scripts tests weekly_reports design_specs
   ```

3. Secrets 등록 (GitHub UI)
   ```
   Settings → Secrets and variables → New repository secret
   ```

4. 첫 번째 Workflow 파일 업로드
   ```
   .github/workflows/monday-self-diagnosis.yml
   ```

---

## 문서 참조

- 📄 **README.md**: 프로젝트 개요
- 📄 **ARCHITECTURE.md**: 상세 아키텍처
- 📄 **SETUP.md**: 설치 & 설정 가이드
- 📄 **API.md**: 함수 & 클래스 레퍼런스

---

**파일 작성일**: 2026-06-23  
**대상**: Jr. TRANG + Sr. TRANG + 개발팀  
**상태**: ✅ 실행 준비 완료  
**다음**: GitHub Actions YAML 파일 생성

---

> **"Jr. TRANG은 이제 완전히 자율적으로 성장할 준비가 되었습니다."**
> — CEO re.eul
