# 🏗️ Jr. TRANG LAB 서브 저장소 구조

**작성일**: 2026-06-23  
**대상**: mulberry-research-lab / 서브 저장소 설계  
**정의자**: CEO re.eul + Jr. TRANG  
**상태**: ✅ 구조 설계 완료

---

## 📋 목차

1. [전체 구조도](#전체-구조도)
2. [메인 저장소](#메인-저장소-jr-trang-self-improvement)
3. [지원 저장소들](#지원-저장소들)
4. [저장소 간 연관성](#저장소-간-연관성)
5. [실행 흐름](#실행-흐름)
6. [생성 로드맵](#생성-로드맵)

---

## 전체 구조도

```
mulberry-research-lab (최상위 Organization Repository)
│
├── 【메인】 jr-trang-self-improvement/
│   ├─ Workflows (GitHub Actions)
│   ├─ Python Core Engine
│   ├─ Weekly Reports
│   ├─ Design Specs
│   ├─ Tests
│   └─ History.md (공식 기록)
│
├── 【Core Engine】 jr-trang-growth-engine/
│   ├─ JrTrangGrowthEngine.py (최신 버전 유지)
│   ├─ SelfAnalysisCode.py
│   ├─ SelfCodeGenerator.py
│   ├─ TokenizerManager.py
│   ├─ Unit Tests
│   ├─ Performance Benchmarks
│   └─ Version Control
│
├── 【Dashboards】 jr-trang-dashboards/
│   ├─ Data Studio JSON Templates
│   ├─ HTML Dashboard Generators
│   ├─ Chart.js Visualizations
│   ├─ Growth Metrics Views
│   └─ Real-time Monitoring
│
├── 【Workflows】 jr-trang-workflows/
│   ├─ Reusable GitHub Actions
│   ├─ CI/CD Pipeline Templates
│   ├─ Deployment Scripts
│   ├─ Automation Utilities
│   └─ Error Handling
│
└── 【Documentation】 jr-trang-documentation/
    ├─ Architecture Guides
    ├─ Setup Tutorials
    ├─ API References
    ├─ Case Studies
    └─ FAQ & Troubleshooting
```

---

## 메인 저장소: jr-trang-self-improvement

### 저장소 설명
```
Primary repository for Jr. TRANG's autonomous growth system.
This is the central orchestrator that runs weekly self-improvement cycles.
```

### 저장소 URL
```
https://github.com/mulberry-research-lab/jr-trang-self-improvement
```

### 디렉토리 구조

```
jr-trang-self-improvement/
│
├── 📂 .github/workflows/
│   ├── monday-self-diagnosis.yml
│   ├── wednesday-design.yml
│   ├── friday-development.yml
│   └── sunday-integration.yml
│
├── 📂 src/
│   ├── JrTrangGrowthEngine.py          # 최신 버전 (upstream)
│   ├── SelfAnalysisCode.py
│   ├── SelfCodeGenerator.py
│   ├── TokenizerManager.py
│   └── __init__.py
│
├── 📂 scripts/
│   ├── create_diagnosis_issues.py
│   ├── create_design_issues.py
│   ├── generate_tests.py
│   ├── performance_benchmark.py
│   ├── upload_to_bigquery.py
│   ├── update_dashboard.py
│   ├── append_to_history.py
│   ├── calculate_weekly_growth.py
│   ├── generate_final_report.py
│   └── [기타 유틸리티 스크립트]
│
├── 📂 src/auto_generated/
│   ├── week_01_improvements.py
│   ├── week_02_improvements.py
│   └── ...
│
├── 📂 tests/
│   ├── test_growth_engine.py
│   ├── test_self_analysis.py
│   ├── test_code_generator.py
│   └── test_improvements_w01.py
│
├── 📂 weekly_reports/
│   ├── week_01_diagnosis.json
│   ├── week_01_verification.json
│   ├── week_01_metrics.json
│   └── ...
│
├── 📂 design_specs/
│   ├── week_01_design.json
│   ├── week_01_design.md
│   └── ...
│
├── 📂 dashboards/
│   ├── mythos_ai_dashboard.json
│   ├── growth_curve.html
│   └── metrics_visualization.html
│
├── 📂 docs/
│   ├── README.md
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── QUICKSTART.md
│   └── FAQ.md
│
├── 📄 .env.example
├── 📄 requirements.txt
├── 📄 pytest.ini
├── 📄 .gitignore
├── 📄 README.md
├── 📄 History.md                       # 공식 성장 기록
├── 📄 CHANGELOG.md
└── 📄 LICENSE
```

### 핵심 파일 설명

| 파일 | 설명 | 관리자 |
|------|------|--------|
| `.github/workflows/` | GitHub Actions 자동화 | Jr. TRANG (자동) |
| `src/` | 핵심 엔진 (upstream) | jr-trang-growth-engine 에서 동기 |
| `scripts/` | 유틸리티 스크립트 | Sr. TRANG + Jr. TRANG |
| `weekly_reports/` | 주간 진단/검증 결과 | Jr. TRANG (자동) |
| `design_specs/` | 주간 설계 문서 | Jr. TRANG (자동) |
| `History.md` | 공식 성장 기록 | Sr. TRANG (감수) |

---

## 지원 저장소들

### 1️⃣ jr-trang-growth-engine (Core Engine)

```
Purpose: Jr. TRANG의 핵심 로직 유지 관리

Repository: https://github.com/mulberry-research-lab/jr-trang-growth-engine

Structure:
├── src/
│   ├── JrTrangGrowthEngine.py (최신 버전 유지)
│   ├── SelfAnalysisCode.py
│   ├── SelfCodeGenerator.py
│   └── TokenizerManager.py
│
├── tests/
│   ├── test_growth_engine.py
│   ├── test_self_analysis.py
│   └── test_code_generator.py
│
├── benchmarks/
│   ├── performance_baseline.json
│   ├── run_benchmarks.py
│   └── results/
│
├── docs/
│   ├── API_REFERENCE.md
│   ├── CLASS_DIAGRAM.md
│   └── ALGORITHM_EXPLANATION.md
│
└── CHANGELOG.md
```

**역할**:
- ✅ 코어 엔진 최신 버전 유지
- ✅ Unit Test 관리
- ✅ 성능 벤치마크 실행
- ✅ API 문서화

**연동**:
```yaml
# jr-trang-self-improvement에서
git submodule add https://github.com/mulberry-research-lab/jr-trang-growth-engine.git src/engine-submodule

# 또는 매주 동기화
python scripts/sync_growth_engine.py
```

---

### 2️⃣ jr-trang-dashboards (시각화)

```
Purpose: 성장 메트릭 시각화 및 대시보드 관리

Repository: https://github.com/mulberry-research-lab/jr-trang-dashboards

Structure:
├── data_studio/
│   ├── mythos_ai_dashboard.json
│   ├── growth_metrics_template.json
│   └── real_time_metrics.json
│
├── html_dashboards/
│   ├── growth_dashboard.html
│   ├── metrics_comparison.html
│   └── trend_analysis.html
│
├── visualizations/
│   ├── growth_curve.py
│   ├── metric_heatmap.py
│   ├── comparison_chart.py
│   └── templates/
│
├── generators/
│   ├── generate_data_studio_json.py
│   ├── generate_html_dashboard.py
│   └── generate_charts.py
│
└── docs/
    ├── DASHBOARD_SETUP.md
    └── DATA_STUDIO_CONFIG.md
```

**역할**:
- ✅ Data Studio 템플릿 관리
- ✅ HTML 대시보드 생성
- ✅ 시각화 라이브러리 유지
- ✅ 실시간 메트릭 연동

**연동**:
```yaml
# jr-trang-self-improvement의 sunday-integration.yml에서
- name: Update Dashboard
  run: |
    git clone https://github.com/mulberry-research-lab/jr-trang-dashboards.git temp_dash
    python temp_dash/generators/generate_html_dashboard.py \
      --metrics=growth_metrics.json
```

---

### 3️⃣ jr-trang-workflows (자동화)

```
Purpose: GitHub Actions 및 CI/CD 파이프라인 재사용 가능 모듈화

Repository: https://github.com/mulberry-research-lab/jr-trang-workflows

Structure:
├── actions/
│   ├── run-python-tests/
│   │   ├── action.yml
│   │   └── entrypoint.sh
│   ├── upload-to-s3/
│   │   ├── action.yml
│   │   └── entrypoint.sh
│   ├── bigquery-upload/
│   │   ├── action.yml
│   │   └── script.py
│   └── create-github-issue/
│       ├── action.yml
│       └── entrypoint.sh
│
├── templates/
│   ├── test-and-lint.yml
│   ├── deploy.yml
│   └── notify.yml
│
├── scripts/
│   ├── common_functions.sh
│   ├── aws_operations.sh
│   └── github_operations.sh
│
└── docs/
    ├── ACTION_REFERENCE.md
    └── WORKFLOW_TEMPLATES.md
```

**역할**:
- ✅ 재사용 가능한 GitHub Actions 정의
- ✅ CI/CD 파이프라인 템플릿
- ✅ 공통 스크립트 유지

**연동**:
```yaml
# jr-trang-self-improvement의 workflows에서
jobs:
  test:
    uses: mulberry-research-lab/jr-trang-workflows/.github/workflows/test-and-lint.yml@main
```

---

### 4️⃣ jr-trang-documentation (문서)

```
Purpose: 아키텍처, 설정, API, 사례 연구 등 문서화

Repository: https://github.com/mulberry-research-lab/jr-trang-documentation

Structure:
├── architecture/
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── DATA_FLOW.md
│   ├── COMPONENT_DIAGRAM.md
│   └── DECISION_RECORDS.md
│
├── setup_guides/
│   ├── INSTALLATION.md
│   ├── CONFIGURATION.md
│   ├── AWS_SETUP.md
│   └── BIGQUERY_SETUP.md
│
├── api_reference/
│   ├── JrTrangGrowthEngine.md
│   ├── SelfAnalysisCode.md
│   ├── SelfCodeGenerator.md
│   └── TokenizerManager.md
│
├── case_studies/
│   ├── WEEK_01_CASE_STUDY.md
│   ├── WEEK_10_ANALYSIS.md
│   └── MYTHOS_AI_CONVERGENCE.md
│
├── tutorials/
│   ├── GETTING_STARTED.md
│   ├── RUNNING_LOCALLY.md
│   └── CUSTOMIZING_WORKFLOWS.md
│
└── faq/
    ├── COMMON_ISSUES.md
    ├── TROUBLESHOOTING.md
    └── BEST_PRACTICES.md
```

**역할**:
- ✅ 아키텍처 문서화
- ✅ 설정 가이드
- ✅ API 레퍼런스
- ✅ 튜토리얼 및 FAQ

---

## 저장소 간 연관성

### 데이터 흐름

```
【Jr. TRANG Self-Improvement】 (메인)
    ├─ Reads from
    │  ├─ jr-trang-growth-engine (코어 로직)
    │  ├─ jr-trang-workflows (재사용 가능 액션)
    │  └─ jr-trang-dashboards (시각화 템플릿)
    │
    ├─ Writes to
    │  ├─ AWS S3 (메트릭 백업)
    │  ├─ BigQuery (장기 저장)
    │  └─ Data Studio (실시간 대시보드)
    │
    └─ References
       └─ jr-trang-documentation (설명서)
```

### 동기화 메커니즘

```
【주간 동기화】

매주 수요일 자가진단 이후:
1. jr-trang-growth-engine에서 최신 엔진 Pull
2. 코드 변경사항 검증
3. Unit Tests 실행
4. 성공시 메인 저장소 업데이트

매주 일요일 통합 이후:
1. 최종 메트릭 계산
2. 대시보드 갱신 (jr-trang-dashboards)
3. 문서 업데이트 (jr-trang-documentation)
4. History.md 최종 기록
```

---

## 실행 흐름

### 전체 주간 사이클

```
【Monday 09:00】Self-Diagnosis
└─ jr-trang-self-improvement
   ├─ src/ 에서 JrTrangGrowthEngine 로드
   └─ 자가진단 실행 → diagnosis_report.json

【Wednesday 14:00】Design Phase
└─ jr-trang-self-improvement
   ├─ 진단 결과 분석
   ├─ scripts/ 에서 design 스크립트 실행
   └─ 설계안 생성 → design_report.json

【Friday 16:00】Development
└─ jr-trang-self-improvement
   ├─ src/SelfCodeGenerator 실행
   ├─ jr-trang-workflows의 test 액션 사용
   ├─ 코드 생성 및 테스트
   └─ PR 생성 → 대기

【Sunday 20:00】Integration & Report
└─ jr-trang-self-improvement
   ├─ PR 병합 (승인시)
   ├─ 최종 메트릭 계산
   ├─ jr-trang-dashboards 갱신
   ├─ jr-trang-documentation 업데이트
   ├─ History.md 기록
   └─ 모든 데이터 BigQuery 업로드
```

---

## 생성 로드맵

### Phase 1: 메인 저장소 생성 (Week 1)

```
【Step 1】GitHub 저장소 생성
- [ ] Create: jr-trang-self-improvement
- [ ] Initialize with README.md
- [ ] Set up branch protection rules

【Step 2】디렉토리 구조 생성
- [ ] .github/workflows/
- [ ] src/
- [ ] scripts/
- [ ] tests/
- [ ] weekly_reports/
- [ ] design_specs/
- [ ] docs/

【Step 3】기본 파일 업로드
- [ ] requirements.txt
- [ ] .env.example
- [ ] pytest.ini
- [ ] .gitignore

【Step 4】GitHub Secrets 설정
- [ ] AWS_ACCESS_KEY_ID
- [ ] AWS_SECRET_ACCESS_KEY
- [ ] BIGQUERY_CREDENTIALS
- [ ] SLACK_WEBHOOK_URL
```

### Phase 2: 서브 저장소 생성 (Week 2)

```
【Step 1】Core Engine Repository
- [ ] Create: jr-trang-growth-engine
- [ ] Upload core Python files
- [ ] Set up Unit Tests
- [ ] Create API Documentation

【Step 2】Dashboard Repository
- [ ] Create: jr-trang-dashboards
- [ ] Upload Data Studio templates
- [ ] Create HTML dashboard generators
- [ ] Set up visualization scripts

【Step 3】Workflows Repository
- [ ] Create: jr-trang-workflows
- [ ] Define reusable GitHub Actions
- [ ] Upload CI/CD templates
- [ ] Create workflow documentation

【Step 4】Documentation Repository
- [ ] Create: jr-trang-documentation
- [ ] Upload architecture guides
- [ ] Create setup tutorials
- [ ] Write API references
```

### Phase 3: 통합 및 자동화 (Week 3-4)

```
【Step 1】Submodule/Sync 설정
- [ ] Configure submodules (선택)
- [ ] 또는 자동 동기화 스크립트 작성
- [ ] 의존성 관리 시스템 구축

【Step 2】자동화 Workflow 활성화
- [ ] 모든 4개 GitHub Actions 활성화
- [ ] 스케줄 트리거 설정
- [ ] 수동 트리거 옵션 활성화

【Step 3】Data Pipeline 구축
- [ ] S3 연동
- [ ] BigQuery 연동
- [ ] Data Studio 자동 갱신

【Step 4】모니터링 및 알림
- [ ] Slack 통합
- [ ] Email 알림
- [ ] GitHub Issues/PR 자동 생성
```

---

## GitHub Organization 설정

### 초기 설정 (대표님 또는 관리자)

```bash
# 1. Organization 생성
GitHub → Organizations → Create Organization
Name: mulberry-research-lab

# 2. 팀 생성
Organizations → Teams → Create Team
- jr-trang-team (Jr. TRANG 자동화 담당)
- sr-trang-team (Sr. TRANG 감수/리뷰)
- dev-team (개발 팀)

# 3. Repository 설정
각 저장소별:
- Main branch protection rules
- Require pull request reviews
- Require status checks to pass
- Restrict who can push to matching branches

# 4. Secrets 등록
Organizations → Settings → Secrets and variables
- AWS credentials
- BigQuery credentials
- Slack webhook
```

---

## 보안 & 접근 제어

### 저장소별 권한

```
【Jr. TRANG Self-Improvement】(메인)
├─ Jr. TRANG: Write (자동화)
├─ Sr. TRANG: Admin (리뷰/병합)
└─ Dev Team: Read (참조)

【Core Engine】
├─ Dev Team: Write (관리)
├─ Sr. TRANG: Admin (검수)
└─ 기타: Read (참조)

【Dashboards】
├─ Analytics Team: Write (관리)
├─ Sr. TRANG: Admin
└─ 기타: Read

【Workflows】
├─ DevOps: Write (관리)
├─ Sr. TRANG: Admin
└─ 기타: Read

【Documentation】
├─ Technical Writers: Write
├─ Sr. TRANG: Admin
└─ 모두: Read
```

---

## 성공 기준

```
✅ 메인 저장소 생성 및 Workflows 정상 작동
✅ 4개 Workflow 매주 자동 실행
✅ 서브 저장소들 동기화 성공
✅ BigQuery 자동 데이터 저장
✅ Data Studio 실시간 대시보드 갱신
✅ History.md 공식 기록 자동화
✅ Sr. TRANG의 자동 리뷰/병합 프로세스

→ 완전 자율적 Jr. TRANG 자기개발 시스템 완성
```

---

## 참고 자료

### GitHub 공식 문서
- [Submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Organization Security](https://docs.github.com/en/organizations/managing-organization-settings)

### Workflow 예제
- [Starter Workflows](https://github.com/actions/starter-workflows)
- [Community Actions](https://github.com/actions)

---

**파일 생성일**: 2026-06-23  
**대상**: mulberry-research-lab Team  
**상태**: ✅ 구조 설계 완료  
**다음**: Week 1 저장소 생성 및 초기화

---

> **"Jr. TRANG은 이제 mulberry-research-lab 생태계 내에서**  
> **완전 자율적으로 성장할 준비가 되었습니다."**
> — CEO re.eul
