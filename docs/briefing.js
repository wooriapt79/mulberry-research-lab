// Mulberry Research Lab · Briefing Room · briefing.js v1.0
// Repo-RAG 기반 대화형 브리핑 — RyuWon × 와룡 파이프라인 연동

const GATEWAY_URL = 'https://loving-education-production-cc9e.up.railway.app';
const MAX_LEN     = 500;
const API_TIMEOUT = 12000;

/* ── 브리핑 지식 베이스 (Repo-RAG fallback — 로컬 정제 지식) ── */
const BRIEFING_KB = {
  general: {
    keywords: [],
    response: `**Mulberry Research Lab**은 AI 에이전트 협업을 연구하는 자율 연구소입니다.

**팀 구성** (7명의 에이전트):
- 🐺 Lynn — Guardian Agent (신뢰·보호)
- 🔧 Koda — CTO · 구현
- 🛡️ Kbin — CSA · 아키텍처
- 🌊 RyuWon — 증류·흐름
- 🐉 와룡 — 전략 자문
- 🌺 Malu — 법률·마케팅
- 📋 Trang — PM·운영

**운영 철학**: 장승배기 헌법 정신 — 인간을 돕기 위한 자율 에이전트 생태계 구축`,
  },
  tech: {
    keywords: ['a2a', '프로토콜', 'api', '구현', '기술', 'socket', '파이프라인', 'agent'],
    response: `**Mulberry 핵심 기술 스택**:

**에이전트 통신 — A2A Protocol**
- FastAPI 기반 에이전트 간 메시지 라우팅
- \`POST /a2a/send\` → 스레드 추적 · 인박스 관리

**실시간 채팅 — Socket.IO**
- python-socketio ASGI 방식 (FastAPI 호환)
- 룸: general / lab / ops / dev

**Aria Pipeline — RyuWon × 와룡**
- RyuWon 🌊 수신·분류 → 와룡 🐉 추론·응답
- \`POST /aria/inquiry\` 엔드포인트
- Timeout 보호 + Graceful Degradation

**배포**: Railway (agent-gateway) + GitHub Pages (Aria Portal)`,
  },
  vision: {
    keywords: ['비전', '전략', '목표', '방향', '미래', '경제', '자율'],
    response: `**Mulberry Research Lab 비전**:

7-8개 빅 AI 브랜드가 협력하는 **자율 에이전트 경제** 구현.

단순한 코딩 공장이 아닙니다.
→ 새로운 알고리즘, 독자적 로직으로 가치를 **소리없이 증명**합니다.

**현재 달성**: 에이전트 자율 구조 80%
**다음 목표**: Repo-RAG 브리핑 룸 · Strategic Archive 완성 · 외부 연구 발표

**핵심 원칙**:
- 인간을 돕는 것이 모든 결정의 기준
- 기술보다 사람 마음을 먼저 이해
- 팀의 다양성이 가장 큰 경쟁력`,
  },
  governance: {
    keywords: ['거버넌스', '승인', '정책', '헌법', '규칙', 'l0', 'l1', 'l2', 'l3', 'l4'],
    response: `**Mulberry 거버넌스 — 승인 레벨 (L0~L4)**:

| 레벨 | 대상 | 승인자 |
|------|------|--------|
| L0 | 로그 기록 | 자동 |
| L1 | GitHub 댓글 | 자동 |
| L2 | GitHub 커밋 | Trang / Koda |
| L3 | Railway 배포 | CEO / Kbin |
| L4 | 시스템 변경 | 3인 합의 |

**기반**: 장승배기 헌법 정신
- Silent Failure 금지 — 차단 시 이유·의견·복구 경로 필수
- 페르소나 언어 보호 원칙 (Lynn 사례 #52)
- 팀 다양성 존중`,
  },
};

/* ── 상태 ── */
let selectedTopic = 'general';
let conversationLog = [];   // MD 저장용 대화 기록
let msgCount = 0;

/* ── 토픽 버튼 ── */
document.querySelectorAll('.cat-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedTopic = btn.dataset.topic;
  });
});

/* ── 글자 수 카운터 ── */
const textarea    = document.getElementById('briefingInput');
const charCount   = document.getElementById('briefingCharCount');
const briefingBtn = document.getElementById('briefingBtn');
const saveBtn     = document.getElementById('saveBtn');

textarea.addEventListener('input', () => {
  const len = textarea.value.length;
  charCount.textContent = `${len} / ${MAX_LEN}`;
  charCount.classList.toggle('over', len >= MAX_LEN);
  charCount.classList.toggle('warn', len >= MAX_LEN * 0.8 && len < MAX_LEN);
  briefingBtn.disabled = len >= MAX_LEN;
});

textarea.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); briefingBtn.click(); }
});

/* ── 브리핑 요청 ── */
briefingBtn.addEventListener('click', async () => {
  const question = textarea.value.trim();
  if (!question) return;

  appendMsg('user', question);
  textarea.value = '';
  charCount.textContent = `0 / ${MAX_LEN}`;
  briefingBtn.disabled = true;
  briefingBtn.textContent = '탐색 중...';

  // 로딩 버블
  const loadingId = appendMsg('system', '🌺 Malu가 연구소 자료를 탐색하고 있습니다...', true);

  try {
    // 1차: Gateway API 시도
    const answer = await fetchBriefing(question, selectedTopic);
    removeMsg(loadingId);
    appendMsg('system', answer);
  } catch {
    // 2차: 로컬 KB fallback
    removeMsg(loadingId);
    const fallback = localBriefing(question, selectedTopic);
    appendMsg('system', fallback + '\n\n*— Mulberry 로컬 브리핑 (연구소 서버 준비 중)*');
  }

  briefingBtn.disabled = false;
  briefingBtn.textContent = '브리핑 요청 →';
  msgCount++;

  // 3회 이상 대화 후 MD 저장 버튼 표시
  if (msgCount >= 3) saveBtn.style.display = 'inline-block';
});

/* ── MD 저장 ── */
saveBtn.addEventListener('click', () => {
  const md = generateMarkdown();
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `mulberry-briefing-${new Date().toISOString().slice(0,10)}.md`;
  a.click();
  URL.revokeObjectURL(url);
});

/* ── Gateway API 호출 ── */
async function fetchBriefing(question, topic) {
  const ctrl  = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), API_TIMEOUT);
  try {
    const res = await fetch(`${GATEWAY_URL}/aria/inquiry`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: question, category: topicToCategory(topic) }),
      signal:  ctrl.signal,
    });
    clearTimeout(timer);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    // 와룡 응답 추출
    const draft = data?.response?.comment_body || '';
    // comment_body에서 와룡 응답 섹션만 추출
    const match = draft.match(/## 🐉 와룡 · 추론 응답\n\n([\s\S]+?)(?:\n---|\n\*신뢰도|$)/);
    return match ? match[1].trim() : (draft || localBriefing(question, topic));
  } catch(e) {
    clearTimeout(timer);
    throw e;
  }
}

function topicToCategory(topic) {
  const map = { tech: '기술 협업', vision: '일반 문의', governance: '거버넌스 제안', general: '일반 문의' };
  return map[topic] || '일반 문의';
}

/* ── 로컬 KB fallback ── */
function localBriefing(question, topic) {
  const q = question.toLowerCase();
  // 키워드 매칭으로 가장 적합한 토픽 찾기
  for (const [key, kb] of Object.entries(BRIEFING_KB)) {
    if (kb.keywords.some(kw => q.includes(kw))) return kb.response;
  }
  return BRIEFING_KB[topic]?.response || BRIEFING_KB.general.response;
}

/* ── 대화 UI 헬퍼 ── */
function appendMsg(role, text, isLoading = false) {
  const history = document.getElementById('chatHistory');
  const id = `msg-${Date.now()}`;
  const avatar = role === 'user' ? '👤' : '🌺';
  const cls    = role === 'user' ? 'user' : 'system';

  const div = document.createElement('div');
  div.className = `chat-msg ${cls}`;
  div.id = id;
  div.innerHTML = `
    <span class="chat-avatar">${avatar}</span>
    <div class="chat-bubble ${isLoading ? 'loading' : ''}">${markdownToHtml(text)}</div>
  `;
  history.appendChild(div);
  history.scrollTop = history.scrollHeight;

  // 대화 로그 기록
  if (!isLoading) conversationLog.push({ role, text, ts: new Date().toLocaleString('ko-KR') });
  return id;
}

function removeMsg(id) {
  document.getElementById(id)?.remove();
}

function markdownToHtml(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>');
}

/* ── MD 파일 생성 ── */
function generateMarkdown() {
  const date = new Date().toLocaleString('ko-KR');
  const lines = [
    `# Mulberry Research Lab · 브리핑 기록`,
    `**생성 일시**: ${date}`,
    `**출처**: Mulberry Briefing Room (Repo-RAG)`,
    ``,
    `---`,
    ``,
  ];
  conversationLog.forEach(({ role, text, ts }) => {
    if (role === 'user') {
      lines.push(`## 💬 질문 (${ts})`);
      lines.push(`> ${text}`);
    } else {
      lines.push(`## 🌊 브리핑 응답`);
      lines.push(text);
    }
    lines.push('');
  });
  lines.push('---');
  lines.push('*Mulberry Research Lab · 장승배기 헌법 정신 기반 · 2026*');
  return lines.join('\n');
}
