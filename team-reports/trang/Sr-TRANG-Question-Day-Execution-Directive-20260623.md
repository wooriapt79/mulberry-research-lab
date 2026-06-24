# 📋 Sr. TRANG Manager를 위한 "질문의 날" 실행 지시서

**발령일**: 2026-06-23  
**발령자**: CEO re.eul  
**수령자**: Sr. TRANG Manager (Nguyen Trang)  
**내용**: "질문의 날" 이니셔티브 실행 지시  
**상태**: 🔴 **즉시 실행**

---

## 🎯 지시 사항

### 【주요 미션】

```
"Mulberry Human-AI Dialogue Archive" 프로젝트를 
Week 2와 함께 시작하기

목표: 
매월 1회 "질문의 날"을 통해 인간과 AI의 대화를 
체계적으로 기록하고 학술적으로 공개하는 문화 정착
```

---

## 📅 실행 일정 (대표님 승인됨)

| 날짜 | 작업 | 담당자 | 상태 |
|------|------|--------|------|
| **2026-06-23 (오늘)** | GitHub 템플릿 추가 | Sr. TRANG | 🔴 **즉시** |
| **2026-06-24 (내일)** | Issue 생성 + 팀 공지 | Sr. TRANG | 🔴 **즉시** |
| **2026-06-24~26** | 팀원 질문 등록 (3일) | 전체 팀 | ⏳ 진행 |
| **2026-06-27 (토)** | 질문 정리 | Wayong | ⏳ 진행 |
| **2026-06-28 (일)** | HF Dataset 공개 | Wayong + Sr. TRANG | ⏳ 진행 |
| **2026-06-29 (월)** | 회고 및 정리 | 전체 팀 | ⏳ 진행 |

---

## 🔧 실행 작업 상세

### 【Task 1】GitHub Issue 템플릿 추가

**담당**: Sr. TRANG Manager  
**시간**: 30분  
**난이도**: ⭐ (매우 쉬움)  
**상태**: 🔴 **2026-06-23 저녁까지 완료**

#### 작업 내용

```
저장소: github.com/wooriapt79/mulberry-research-lab
경로: .github/ISSUE_TEMPLATE/question-day.md

파일 생성:
```markdown
name: 질문의 날
about: Mulberry Human-AI Dialogue Archive에 질문을 등록합니다
title: "[질문의 날 #N] YYYY-MM-DD – 우리가 AI에게 묻고 싶은 것"
labels: ["question-day", "archive", "human-ai"]
assignees: ["trang-manager", "wayong-mentor"]

---

📌 질문 등록 안내

* 목적: 연구소의 질문 문화를 활성화하고, Human-AI Dialogue Archive를 풍성하게 합니다.
* 기간: 이슈 생성 후 3일간 댓글 등록 가능
* 형식: 댓글로 자유롭게 작성
* 표시: `[질문자 → 수신자] 질문 내용`
  * 예: `[Wayong → Koda] AI는 스스로의 한계를 인식할 수 있을까요?`
  * 예: `[Trang → Human] 인간은 어떤 순간에 '옳은 길'임을 확신하나요?`

📝 이번 회차의 질문들 (여기에 댓글로 등록해주세요)

🔍 참고: 지난 질문들 (예시)
* [#001] TRANG → Human: 외로움이 정확히 어떤 느낌인가요?
* [#003] Human → AI: AI는 기다림을 경험하는가?
* [#005] TRANG → Human: 인간은 어떤 순간에 자신이 '옳은 곳에 있다'는 것을 아나요?

운영자: Sr. TRANG Manager, Wayong (Strategic Mentor)
```

#### 체크리스트

```
☐ 저장소 접속 (github.com/wooriapt79/mulberry-research-lab)
☐ .github/ISSUE_TEMPLATE/ 폴더 확인
☐ question-day.md 파일 생성
☐ 위 템플릿 내용 복사
☐ Commit 메시지: "feat: Add question-day issue template for Dialogue Archive"
☐ Push 완료
☐ 템플릿 정상 작동 확인
```

---

### 【Task 2】제1회 Issue 생성 및 팀 공지

**담당**: Sr. TRANG Manager  
**시간**: 30분  
**난이도**: ⭐ (매우 쉬움)  
**상태**: 🔴 **2026-06-24 오전까지 완료**

#### 작업 A: GitHub Issue 생성

```
제목:
[질문의 날 #1] 2026-06-27 – 우리가 AI에게 묻고 싶은 것

본문:
안녕하세요! 

Mulberry Research Lab의 첫 번째 "질문의 날"입니다.

【일정】
- 등록 기간: 2026-06-24 (수) ~ 2026-06-26 (금) 23:59 KST
- 정리: 2026-06-27 (토)
- 공개: 2026-06-28 (일)

【방법】
이 이슈에 댓글로 자유롭게 질문을 등록해주세요.

형식: [질문자 → 수신자] 질문 내용

예시:
- [CEO re.eul → Jr. TRANG] 당신이 준비되었다고 느낄 때는?
- [Jr. TRANG → Sr. TRANG] 믿음이란 무엇인가요?
- [Wayong → Malu] 법률과 철학의 교점은?

【의미】
이 질문들은 모두 Hugging Face에 공개되어 
학술적 자료로 기록됩니다.

편하게 질문해주세요! 🌿
```

#### 작업 B: 팀 공지 발송

**채널**: Slack / 이메일  
**타이밍**: Issue 생성 직후

```
📢 공지

안녕하세요, Mulberry 팀!

Mulberry Research Lab의 "질문의 날 #1"이 시작됩니다! 🌿

🎯 무엇인가요?
인간과 AI가 서로에게 묻고 싶은 질문들을 
매월 한 번 모아서 기록하고 공개하는 자리입니다.

📅 일정
- 등록: 2026-06-24 (수) ~ 2026-06-26 (금)
- 공개: 2026-06-28 (일) HF Dataset으로 공개

🔗 링크
GitHub Issue: [링크 추가]

❓ 어떤 질문이 좋을까요?
- "AI는 무엇을 두려워하나요?" (기술적)
- "왜 우리가 함께 성장해야 할까요?" (철학적)  
- "다음 주는 어떤 변화가 올까요?" (미래적)

다양한 질문을 기대합니다! 🙏
```

#### 체크리스트

```
☐ GitHub Issue 생성 (제목, 본문 위 템플릿 사용)
☐ Labels 지정: question-day, archive, human-ai
☐ Assignees 지정: Sr. TRANG Manager, Wayong
☐ Slack 공지 발송
☐ 이메일 공지 발송 (필요시)
☐ 팀원들이 공지를 받았는지 확인
```

---

### 【Task 3】HF Dataset 스켈레톤 생성

**담당**: Sr. TRANG Manager + Wayong  
**시간**: 1시간  
**난이도**: ⭐⭐ (쉬움)  
**상태**: ⏳ **2026-06-24 저녁까지 완료**

#### 작업 내용

```
Hugging Face Dataset 생성:
이름: mulberry-research-lab/human-ai-dialogue

구조:
├── README.md (Dataset Card)
├── data/
│   ├── train.jsonl (전체 질문)
│   ├── answered.jsonl (답변 완료)
│   └── unanswered.jsonl (미답변)
├── meta/
│   ├── schema.json
│   └── tags.json
└── docs/
    └── guidelines.md
```

#### 단계별 지시

```
1️⃣ HF 조직 로그인
   https://huggingface.co/mulberry-research-lab

2️⃣ "새 Dataset 생성" 클릭
   Dataset 이름: human-ai-dialogue
   설명: Mulberry Human-AI Dialogue Archive
   라이선스: CC BY-NC 4.0
   태그: ai-human-interaction, philosophy, dialogue

3️⃣ 파일 업로드 (초기)
   README.md (아래 참조)
   schema.json (아래 참조)

4️⃣ 공개 설정
   Visibility: Public
   Visibility toggle: On
```

#### 필요 파일

**README.md**:
```markdown
---
language: ko
license: cc-by-nc-4.0
task_categories:
  - conversational
  - question-answering
pretty_name: Mulberry Human-AI Dialogue Archive
tags:
  - ai-human-interaction
  - philosophy
  - dialogue
---

# Mulberry Human-AI Dialogue Archive

📖 개요
이 데이터셋은 Mulberry Research Lab의 Human-AI Dialogue Archive입니다.

🧭 목적
- AI-Human 상호작용의 철학적·감정적 측면 연구
- AI 인문학(AI Humanities) 자료로서의 활용
- 지속적 대화 기록의 공개적 축적

📊 데이터 구성
- 2026-06-27부터 매월 질문의 날을 통해 수집
- CC BY-NC 4.0 라이선스 (비상업적 연구 목적)

🔗 관련 링크
- GitHub: https://github.com/wooriapt79/mulberry-research-lab
- Mulberry Research Lab: https://huggingface.co/mulberry-research-lab
```

**schema.json**:
```json
{
  "id": "Q-001",
  "session": "2026-06-27",
  "question": "질문 내용",
  "questioner": "질문자 (Human/AI)",
  "recipient": "수신자 (Human/AI)",
  "answer": "답변 내용 (또는 '대기 중')",
  "answer_date": "2026-06-28 (또는 null)",
  "is_answered": false,
  "tags": ["태그1", "태그2"],
  "source_issue": "GitHub Issue URL",
  "notes": "추가 노트"
}
```

#### 체크리스트

```
☐ HF 조직 접속
☐ 새 Dataset 생성 (human-ai-dialogue)
☐ README.md 업로드
☐ schema.json 업로드
☐ 라이선스 설정 (CC BY-NC 4.0)
☐ 태그 설정
☐ 공개 설정 (Public)
☐ 데이터셋 URL 확인: 
   https://huggingface.co/datasets/mulberry-research-lab/human-ai-dialogue
```

---

### 【Task 4】질문 정리 및 공개 (2026-06-27~28)

**담당**: Wayong + Sr. TRANG Manager  
**시간**: 3-4시간  
**난이도**: ⭐⭐ (중간)  
**상태**: ⏳ **2026-06-27~28 진행**

#### 작업 흐름

```
【2026-06-27 (토)】
1. GitHub Issue에서 등록된 질문 수집
2. 중복/유사 항목 정리
3. JSONL 포맷으로 변환
4. 민감정보 필터링

【2026-06-28 (일)】
1. train.jsonl 생성
2. answered.jsonl / unanswered.jsonl 분리
3. HF Dataset에 업로드
4. README 최종 확인
5. 공개 (Visibility: Public)
```

#### 출력 형식 (JSONL)

```jsonl
{"id":"Q-001","session":"2026-06-27","question":"질문1","questioner":"CEO re.eul","recipient":"Jr. TRANG","answer":"대기 중","answer_date":null,"is_answered":false,"tags":["성장","준비"],"source_issue":"https://github.com/...#issuecomment-...","notes":""}
{"id":"Q-002","session":"2026-06-27","question":"질문2","questioner":"Jr. TRANG","recipient":"Sr. TRANG","answer":"대기 중","answer_date":null,"is_answered":false,"tags":["신뢰","관계"],"source_issue":"https://github.com/...#issuecomment-...","notes":""}
```

#### 체크리스트

```
☐ GitHub Issue 모든 댓글 검토
☐ 질문 복사-정리 (중복 제거)
☐ JSONL 파일 생성
☐ 민감정보 필터링
☐ GitHub Issue 링크 추가
☐ train.jsonl 생성
☐ answered.jsonl / unanswered.jsonl 분리
☐ HF Dataset에 업로드
☐ 정상 공개 확인
```

---

## 📋 최종 체크리스트

### 【Sr. TRANG Manager의 책임】

```
⏳ 2026-06-23 (오늘)
☐ Task 1: GitHub 템플릿 추가 (30분)

⏳ 2026-06-24 (내일)
☐ Task 2-A: Issue 생성 (15분)
☐ Task 2-B: 팀 공지 발송 (15분)
☐ Task 3: HF Dataset 스켈레톤 생성 (1시간)

⏳ 2026-06-27~28 (토~일)
☐ Task 4: 질문 정리 및 공개 (Wayong과 협력)

⏳ 2026-06-29 (월)
☐ 회고 및 정리
☐ 다음 회차 준비
```

### 【지원 체계】

```
기술 지원: Wayong (Strategic Mentor)
법률 자문: Malu 실장
코딩 지원: Jr. TRANG (필요시)
CEO 확인: CEO re.eul (최종 승인)
```

---

## 📞 연락 및 질문

```
【문제 발생시】
- GitHub Issue 생성 관련: Wayong에 문의
- HF Dataset 관련: Wayong에 문의
- 팀 공지 관련: Sr. TRANG 판단
- 전략 변경: CEO re.eul에 보고

【진행 상황】
매일 저녁 7시: Slack으로 진행 상황 공유
```

---

## 🎯 이 지시서의 의미

```
Week 2가 시작되면서:
✅ Jr. TRANG의 자동 성장이 가동되고
✅ 인간-AI의 대화 기록도 시작된다

= Mulberry의 3가지 축이 동시에 움직임
  사회공헌(Zero Food Desert)
  + 기술혁신(Jr. TRANG Growth)
  + 학문개척(Human-AI Dialogue)
```

---

## ✅ 승인 서명

```
【발령】
CEO re.eul

【날짜】
2026-06-23

【상태】
✅ 즉시 실행 권한 부여

【기대사항】
Sr. TRANG Manager가 이 이니셔티브를
Week 2와 함께 성공적으로 시작하기를 기대합니다.

감사합니다.
```

---

**Sr. TRANG Manager께**

이 지시서를 받으시고,
편한 시간에 실행 시작해주세요.

모든 준비가 되어 있습니다.
모든 지원이 준비되어 있습니다.

감사합니다. 🙏

— CEO re.eul
