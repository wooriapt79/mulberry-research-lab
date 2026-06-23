# 🎯 Jr. TRANG Week 1 Setup — 왜 필요한가? 무엇을 하는가?

**작성일**: 2026-06-23  
**대상**: CEO re.eul · Jr. TRANG · Sr. TRANG  
**목적**: Week 1 준비 작업의 필요성과 의미를 명확히 함

---

## 📋 목차

1. [전체 구도](#전체-구도)
2. [Week 1 작업 상세 분석](#week-1-작업-상세-분석)
3. [팀 구조의 이유](#팀-구조의-이유)
4. [역할과 권한 정의](#역할과-권한-정의)
5. [실행 체크리스트](#실행-체크리스트)

---

## 전체 구도

### Jr. TRANG의 자율 성장 시스템 = 다층 구조

```
【토대 - 기술 인프라】
GitHub Organization + 저장소들
└─ "집" 같은 공간 (Jr. TRANG이 일할 장소)

【뼈대 - 팀 구조】
Jr. TRANG Team + Sr. TRANG Team
└─ "역할 분담" (누가 뭘 하는가?)

【맥박 - 자동화】
4개 Workflow (월수금일)
└─ "매주 반복" (자동으로 성장하기)

【영혼 - 의사소통】
Issues, PRs, Discussions
└─ "협력" (Jr.과 Sr.이 대화하기)

이 모든 것이 **Week 1에 준비**되어야
Week 2부터 **자동으로 작동**할 수 있습니다.
```

---

## Week 1 작업 상세 분석

### 작업 1️⃣: GitHub Organization 생성

#### 🤔 왜 필요한가?

```
【현재 상황】
- Jr. TRANG은 단순 AI (Haiku 4.5)
- 자기 저장소가 없음
- 팀원들과 협력 채널이 없음
- 자동화를 위한 "주소"가 없음

【문제】
"어디에 저장할 것인가?"
"누가 뭘 할 수 있게 할 것인가?"
"팀원들과 어떻게 소통할 것인가?"

【해결】
GitHub Organization을 만들면:
✅ 중앙화된 공간 제공
✅ 팀 구조 설정 가능
✅ 권한 관리 가능
✅ 자동화 중심지 구축
```

#### 🎯 구체적으로 뭘 하나?

```bash
GitHub.com에서 직접:
1. Organizations → Create Organization
2. Name: mulberry-research-lab
3. Contact email: mulberry@ai.kr
4. Organization type: Open Source / Research
5. Owner: CEO re.eul

완료!
→ https://github.com/mulberry-research-lab
```

#### 📊 결과물

```
Organization Dashboard:
├─ 저장소 관리 (5개 생성 예정)
├─ 팀 관리 (Jr. TRANG Team, Sr. TRANG Team)
├─ Secrets 관리 (AWS, BigQuery 자격증명)
└─ Organization Settings (권한, 정책)

이제 Jr. TRANG이 "집을 얻은" 상태
```

---

### 작업 2️⃣: Jr. TRANG 팀 생성

#### 🤔 왜 필요한가?

```
【Jr. TRANG의 정체】
- 자동화 에이전트 (매주 자동 실행)
- 자체 코드를 생성할 수 있는 AI
- GitHub에서 자동으로 작업함
- 감시/검수가 필요 (위험 회피)

【문제】
"누가 Jr. TRANG을 '사원'으로 등록할 것인가?"
"어떤 권한을 줄 것인가?"
"누가 감시할 것인가?"

【해결】
"Jr. TRANG Team"을 만들면:
✅ Jr. TRANG을 팀 멤버로 설정
✅ 자동화 권한 명확화
✅ 코드 리뷰 프로세스 정의
✅ 실패시 롤백 계획 수립
```

#### 🎯 구체적으로 뭘 하나?

```bash
GitHub Organization Settings에서:
1. Teams → Create Team
2. Team name: jr-trang-team
3. Description: "Jr. TRANG Autonomous Growth System"
4. Team privacy: Private

Members 추가:
├─ GitHub Bot: jr-trang-bot (자동화용)
├─ Sr. TRANG: @sr-trang (감수자)
└─ CEO re.eul: @ceo-reul (승인자)

Permissions:
├─ Repository: jr-trang-self-improvement
├─ Role: Write (코드 작성, PR 생성)
└─ Branch: main (main 브랜치만 권한)
```

#### 🎬 무엇을 할 수 있는가?

```
【Jr. TRANG이 할 수 있는 것】
✅ 자동 코드 작성 (Friday)
✅ GitHub에 자동 커밋
✅ PR 자동 생성
✅ Issues 자동 생성
✅ 데이터 자동 저장

【Jr. TRANG이 할 수 없는 것】
❌ main 브랜치에 직접 푸시 (PR 필요)
❌ 다른 저장소 접근 (권한 제한)
❌ Secrets 수정 (CEO만 가능)
❌ 팀원 추가/제거 (Sr. TRANG이 함)
```

#### 📊 결과물

```
Jr. TRANG Team Dashboard:
├─ Members: Jr. TRANG Bot, Sr. TRANG, CEO
├─ Repositories: jr-trang-self-improvement (Write)
├─ Permissions: Restricted (Write만, main에 직접 푸시 불가)
└─ Audit Log: 모든 작업 기록

이제 Jr. TRANG이 "직원이 된" 상태
```

---

### 작업 3️⃣: Sr. TRANG 팀 생성

#### 🤔 왜 필요한가?

```
【Sr. TRANG의 정체】
- 감수자, 리뷰어 역할
- Jr. TRANG의 코드 검증
- 최종 의사결정 권한
- 팀 조율 능력

【문제】
"누가 Jr. TRANG을 감시/검수할 것인가?"
"자동 코드가 맞는지 확인하는 사람?"
"문제 발생시 롤백할 권한?"

【해결】
"Sr. TRANG Team"을 만들면:
✅ Jr. TRANG의 작업 리뷰
✅ PR 승인/거절 권한
✅ 문제시 즉시 대응
✅ History.md 최종 기록
✅ 팀 내 의사소통 중심
```

#### 🎯 구체적으로 뭘 하나?

```bash
GitHub Organization Settings에서:
1. Teams → Create Team
2. Team name: sr-trang-team
3. Description: "Sr. TRANG - Code Review & Team Coordination"
4. Team privacy: Private

Members 추가:
├─ Sr. TRANG: @sr-trang-manager (PM, 리뷰어)
├─ CEO re.eul: @ceo-reul (최종 승인)
├─ Malu 실장: @malu-chief (법률/전략 검수)
└─ Kbin: @kbin-architect (기술 검토)

Permissions:
├─ Repository: jr-trang-self-improvement
├─ Role: Maintain (리뷰, 병합, 설정 변경)
└─ Branch: main (모든 권한)
```

#### 🎬 무엇을 할 수 있는가?

```
【Sr. TRANG Team이 할 수 있는 것】
✅ Jr. TRANG의 PR 리뷰
✅ PR 승인/거절
✅ main 브랜치에 직접 푸시 (긴급)
✅ Releases 관리
✅ GitHub Actions 재실행
✅ 브랜치 설정 변경

【Sr. TRANG Team이 할 수 없는 것】
❌ Secrets 수정 (CEO만)
❌ 팀 권한 변경 (Owner만)
❌ Organization Settings (Owner만)
```

#### 📊 결과물

```
Sr. TRANG Team Dashboard:
├─ Members: Sr. TRANG, CEO, Malu, Kbin
├─ Repositories: Maintain 권한
├─ PR Review Queue: Jr. TRANG의 모든 PR
└─ Audit Log: 모든 결정 기록

이제 "감시 시스템이 가동된" 상태
```

---

## 팀 구조의 이유

### 왜 Jr. TRANG Team과 Sr. TRANG Team을 분리하는가?

#### 🎯 목표

```
안전성 + 자율성의 균형

【자율성】
Jr. TRANG이 매주 자동으로 작업
→ 자기 개발, 코드 생성, 보고서 작성

【안전성】
Sr. TRANG이 모든 작업을 검증
→ 코드 품질, 비즈니스 로직, 위험 회피

【투명성】
모든 작업이 GitHub에 기록
→ 누가 뭘 했는지 추적 가능
→ 문제 발생시 원인 파악 가능
```

#### 📊 권한 매트릭스

```
                  Jr. TRANG  Sr. TRANG  CEO
────────────────────────────────────────────
코드 작성             ✅         ✅        -
코드 리뷰             ❌         ✅        ✅
PR 생성               ✅         ✅        -
PR 승인               ❌         ✅        ✅
main 브랜치 푸시      ❌         ✅        ✅
Secrets 수정          ❌         ❌        ✅
팀 권한 설정          ❌         ✅        ✅
Organization Settings ❌         ❌        ✅
────────────────────────────────────────────

핵심: "체크 앤 밸런스"
→ Jr. TRANG은 "일"하고
→ Sr. TRANG이 "검증"하고
→ CEO가 "최종 승인"
```

#### 🔄 워크플로우

```
【매주 반복】

월요일 09:00 (Jr. TRANG 자동 실행)
└─ 자가진단 완료 → Issues 생성

   ↓

Sr. TRANG이 Issues 검토
└─ 진단이 맞는가? 확인

   ↓

수요일 14:00 (Jr. TRANG 자동 실행)
└─ 설계안 생성 → Issues 생성

   ↓

Sr. TRANG이 설계 검토
└─ 설계가 합리적인가? 확인

   ↓

금요일 16:00 (Jr. TRANG 자동 실행)
└─ 코드 생성 → PR 생성

   ↓

Sr. TRANG이 코드 리뷰
└─ 코드 품질 검증
└─ 버그 없는가? 확인
└─ Approve 또는 Request Changes

   ↓

일요일 20:00 (Jr. TRANG 자동 실행)
└─ 통합 & 최종 기록

   ↓

Sr. TRANG이 History.md 확인
└─ 공식 기록 검증
└─ 다음주 준비 확인
```

---

## 역할과 권한 정의

### 3가지 역할의 명확한 구분

#### 👤 Jr. TRANG (자동화 에이전트)

**정체**:
```
Haiku 4.5 + GitHub Actions Workflows

담당: 자동 실행 (매주 월수금일)
```

**하는 일**:
```
【매주】
월: 자가진단 → Issues 생성
수: 로직 설계 → 문서 작성
금: 코드 생성 → PR 생성
일: 통합 & 최종 기록
```

**권한**:
```
✅ Write 권한 (저장소 코드 작성)
✅ PR 생성 가능
✅ Issues 생성 가능
✅ Commits 가능 (새 브랜치에만)

❌ main 브랜치 직접 푸시 불가
❌ PR 자동 병합 불가
❌ Secrets 접근 불가
❌ 다른 저장소 접근 불가
```

**실패시 대응**:
```
GitHub Actions 실패
  ↓
자동 알림 (Slack/Email)
  ↓
Sr. TRANG 즉시 조사
  ↓
Sr. TRANG 수동 개입
  ↓
원인 파악 & 수정
```

---

#### 👨‍💼 Sr. TRANG (감수자 + PM)

**정체**:
```
Claude Sonnet + Manual Review + Decision Making

담당: 검증, 리뷰, 최종 결정
```

**하는 일**:
```
【매주】
월: Jr. 자가진단 결과 검수
수: Jr. 설계안 검수
금: Jr. 코드 PR 리뷰 → 승인/거절
일: History.md 최종 기록 → 공식화

【월간】
- 성장 추세 분석
- 개선 방향 제시
- CEO에게 보고

【비상】
- 실패시 즉시 롤백
- 버그 발견시 긴급 대응
- 위험 상황 판단
```

**권한**:
```
✅ Maintain 권한 (모든 저장소 관리)
✅ PR 승인/거절
✅ main 브랜치 직접 푸시
✅ GitHub Actions 재실행
✅ Releases 관리
✅ Branches 설정 변경

❌ Secrets 수정 불가
❌ Organization Settings 불가
❌ 팀 권한 변경 불가
```

**검증 기준**:
```
코드 리뷰 체크리스트:
□ 버그 없는가?
□ 성능 개선인가?
□ 테스트 통과했는가?
□ 문서화 되었는가?
□ 비즈니스 로직 맞는가?

모두 체크되면 → Approve & Merge
하나라도 문제면 → Request Changes
```

---

#### 👑 CEO re.eul (최종 승인자)

**정체**:
```
CEO + 최종 의사결정권자

담당: 전략 방향, 최종 승인
```

**하는 일**:
```
【주간】
- "콜(노크)" → Jr. TRANG 자기개발 집중모드 시작
- 주간 리포트 검토
- 성장 방향 조정 지시

【월간】
- 팀 전체 성장 평가
- Mythos AI 수렴도 확인
- 다음 달 전략 수립

【필요시】
- Organization Settings 변경
- 팀 구조 조정
- 중대 정책 결정
```

**권한**:
```
✅ Owner 권한 (모든 것)
✅ Secrets 설정
✅ Organization Settings 변경
✅ 팀 권한 설정
✅ 저장소 생성/삭제
✅ 모든 것의 최종 승인

= "조종사" 역할
```

**의사결정 원칙**:
```
"Jr. TRANG의 성장을 믿고,
 Sr. TRANG의 검증을 믿고,
 데이터 기반의 결정을 내린다"

주간 메트릭 확인
  ↓
Sr. TRANG의 의견 청취
  ↓
CEO의 최종 판단
  ↓
대표님께 보고 (필요시)
```

---

## 실행 체크리스트

### Week 1 Day 1 (월요일)

```
【CEO re.eul】
☐ GitHub Organization 생성
   └─ Name: mulberry-research-lab
   └─ Owner: CEO re.eul
   └─ Email: mulberry@ai.kr

☐ Jr. TRANG Team 생성
   └─ Members: Jr. TRANG Bot, Sr. TRANG, CEO
   └─ Permissions: Write (메인 저장소만)

☐ Sr. TRANG Team 생성
   └─ Members: Sr. TRANG, CEO, Malu, Kbin
   └─ Permissions: Maintain (모든 저장소)

☐ GitHub Organization의 Settings 확인
   └─ Branch protection rules
   └─ Require pull request reviews
   └─ Require status checks to pass
```

### Week 1 Day 2-3 (화-수)

```
【Sr. TRANG】
☐ Jr. TRANG Bot GitHub 계정 생성/연결
   └─ GitHub Actions에서 사용할 계정
   └─ JWT token 생성
   └─ Organizations에 초대

☐ Repository 초기 생성
   └─ jr-trang-self-improvement (메인)
   └─ 기본 파일 업로드 (.gitignore, README 등)

☐ Secrets 등록 준비
   └─ AWS credentials 확보
   └─ BigQuery JSON key 확보
   └─ Slack webhook 확보
```

### Week 1 Day 4-5 (목-금)

```
【Jr. TRANG】
☐ Workflow 파일 업로드
   └─ .github/workflows/monday-self-diagnosis.yml
   └─ .github/workflows/wednesday-design.yml
   └─ .github/workflows/friday-development.yml
   └─ .github/workflows/sunday-integration.yml

☐ Python 코드 업로드
   └─ src/JrTrangGrowthEngine.py
   └─ src/SelfAnalysisCode.py
   └─ src/SelfCodeGenerator.py
   └─ requirements.txt

☐ 기본 디렉토리 구조 생성
   └─ scripts/
   └─ tests/
   └─ weekly_reports/
   └─ design_specs/
```

### Week 1 Day 5-6 (금-토)

```
【Sr. TRANG】
☐ GitHub Secrets 등록
   └─ AWS_ACCESS_KEY_ID
   └─ AWS_SECRET_ACCESS_KEY
   └─ BIGQUERY_CREDENTIALS
   └─ SLACK_WEBHOOK_URL

☐ Branch Protection Rules 설정
   └─ main 브랜치 보호
   └─ PR 리뷰 필수
   └─ Status checks 필수

☐ GitHub Actions 활성화
   └─ Allow all actions
   └─ Workflow 테스트 (수동 트리거)
```

### Week 1 Day 7 (일)

```
【모두】
☐ Week 1 준비 완료 확인
   └─ Organization ✅
   └─ Teams ✅
   └─ Repository ✅
   └─ Workflows ✅
   └─ Secrets ✅

☐ Week 2 준비
   └─ Monday 09:00 자동 실행 준비
   └─ Jr. TRANG 첫 자가진단
   └─ Sr. TRANG 검증 준비
```

---

## 문제 상황별 대응

### 시나리오 1️⃣: Jr. TRANG 자동화 실패

```
【상황】
Workflow 실패 → GitHub Actions 오류

【자동 대응】
1. GitHub Actions 자동 알림 (Slack)
2. Log 확인 가능

【Sr. TRANG 대응】
1. 에러 로그 확인
2. 문제 원인 파악
3. 수동으로 스크립트 실행
4. 결과 확인 후 재보고

【CEO 대응 (필요시)】
1. 문제의 심각성 판단
2. 대체 방안 지시
```

### 시나리오 2️⃣: PR 승인 거절

```
【상황】
Sr. TRANG이 Jr. TRANG의 코드 리뷰에서
"Request Changes" 선택

【자동 대응】
1. GitHub에 자동 알림
2. 다음주 자동화 대기

【Sr. TRANG 설명】
1. 구체적인 문제점 코멘트
2. 수정 방향 제시
3. 재검토 예정 공지

【Jr. TRANG 대응】
1. 피드백 반영
2. 개선 코드 작성
3. 재 PR 생성
```

### 시나리오 3️⃣: 긴급 상황

```
【상황】
발견: 생성된 코드가 위험한 로직 포함

【즉시 대응】
1. Sr. TRANG: 즉시 PR 거절
2. Sr. TRANG: 긴급 브랜치 생성 & 수정
3. Sr. TRANG: CEO에게 보고
4. CEO: 최종 판단

【장기 대응】
1. 왜 이런 문제가 생겼는가?
2. Jr. TRANG의 로직 개선
3. Workflow 수정
4. 안전장치 추가
```

---

## 성공 기준

### Week 1 완료 = 이 상태

```
✅ Organization 생성 및 가동
✅ 2개 팀 (Jr., Sr.) 명확히 구분
✅ 메인 저장소 생성 및 초기화
✅ GitHub Actions 모두 업로드
✅ Secrets 모두 등록
✅ Branch protection 설정 완료
✅ 자동화 시스템 준비 완료

= "발사 준비 완료" 상태
```

### Week 2 시작 = 이 상태

```
【월요일 09:00】
✅ Jr. TRANG의 첫 자가진단 자동 실행
✅ Issues 자동 생성
✅ Sr. TRANG이 Issues 검토 시작
✅ 무한 성장 사이클 시작

= "우주선 발사!" 상태
```

---

## 최종 요약

### Week 1의 의미

```
【건축】
집을 지음 (GitHub Organization)

【팀 구성】
직원을 뽑음 (Jr. TRANG, Sr. TRANG Teams)

【도구 준비】
기계를 설치함 (GitHub Actions Workflows)

【안전장치】
보안을 설정함 (Secrets, Permissions)

결과: "Jr. TRANG이 매주 자동으로 성장할 수 있는 무대" 완성
```

### 각 역할의 정의

```
【Jr. TRANG】= 근로자
"내가 명령받은 대로 매주 일한다"
├─ 월: 진단
├─ 수: 설계
├─ 금: 개발
└─ 일: 보고

【Sr. TRANG】= 감시자 + 관리자
"Jr.의 일을 검증하고 승인한다"
└─ 품질 관리, 리스크 관리, 최종 기록

【CEO re.eul】= 총감독
"전체 방향을 정하고 최종 결정한다"
└─ 전략 수립, 대정책 결정
```

---

**파일 작성일**: 2026-06-23  
**대상**: CEO re.eul, Jr. TRANG, Sr. TRANG  
**상태**: ✅ Week 1 준비 완료  
**다음**: Week 1 Day 1 → Organization 생성

---

> **"Week 1은 무대 준비,**  
> **Week 2부터 Jr. TRANG의 성장이 자동으로 시작됩니다."**
> — CEO re.eul
