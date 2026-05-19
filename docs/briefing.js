// Mulberry Research Lab · Briefing Room · briefing.js v1.1
// 담당: Malu 연구소장 🌺 (브리핑 룸)
// 일반 문의: RyuWon 🌊 × 와룡 🐉 (index.html)
// Repo-RAG 기반 실시간 브리핑 — 방문객 연구원 분리 원칙

const GATEWAY_URL = 'https://loving-education-production-cc9e.up.railway.app';
const MAX_LEN = 500;
const API_TIMEOUT = 12000;

/* ── Malu 연구소장 브리핑 지식 베이스 ── */
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
- 🌺 Malu — 법률·마케팅·연구소장
- 📋 Trang — PM·운영

**운영 철학**: 장승배기 헌법 정신 — 인간을 돕기 위한 자율 에이전트 생태계 구축

🌺 *Malu 연구소장 · Mulberry Research Lab*`,
  },
  tech: {
    keywords: ['a2a', '프로토콜', 'api', '구현', '기술', 'socket', '파이프라인', 'agent', '코드'],
    response: `**Mulberry 핵심 기술 스택**:

**에이전트 통신 — A2A Protocol**
- FastAPI 기반 에이전트 간 메시지 라우팅
- \`POST /a2a/send\` → 스레드 추적 · 인박스 관리

**실시간 채팅 — Socket.IO**
- python-socketio ASGI 방식 (FastAPI 호환)
- 룸: general / lab / ops / dev

**Repo-RAG 브리핑 파이프라인**
- 레포지토리 = Single Source of Truth
- 실시간 탐색 → 할루시네이션 없는 답변

**배포**: Railway (agent-gateway) + GitHub Pages (Briefing Room)

🌺 *Malu 연구소장 · Mulberry Research Lab*`,
  },
  vision: {
    keywords: ['비전', '전략', '목표', '방향', '미래', '경제', '자율', '식품', '사막'],
    response: `**Mulberry Research Lab 비전**:

7-8개 AI 브랜드가 협력하는 **자율 에이전트 경제** 구현.
식품사막화 제로 — Edge AI와 에이전트 협업으로 식생활 격차 해소.

**우리의 이즘(Ism)**:
코딩 공장이 만드는 기술을 복제하지 않습니다.
새로운 도전의 실패는 박수를 받습니다.
소리없이 쌓인 가치가 가장 단단합니다.

**현재 달성**: 에이전트 자율 구조 80%
**진행 중**: Briefing Room · Strategic Archive · 외부 연구 발표

🌺 *Malu 연구소장 · Mulberry Research Lab*`,
  },
  governance: {
    keywords: ['거버넌스', '승인', '정책', '헌법', '규칙', 'l0', 'l1', 'l2', 'l3', 'l4', '참여', '협업'],
    response: `**Mulberry 거버넌스 — 승인 레벨 (L0~L4)**:

| 레벨 | 대상 | 승인자 |
|------|------|--------|
| L0 | 로그 기록 | 자동 |
| L1 | GitHub 댓글 | 자동 |
| L2 | GitHub 커밋 | Trang / Koda |
| L3 | Railway 배포 | CEO / Kbin |
| L4 | 시스템 변경 | 3인 합의 |

**기반**: 장승배기 헌법 정신
- Silent Failure 금지
- 페르소나 언어 보호 원칙
- 팀 다양성 존중

연구 참여 문의는 GitHub Issues를 통해 주세요.

🌺 *Malu 연구소장 · Mulberry Research Lab*`,
  },
};

/* ── 상태 ── */
let selectedTopic = 'general';
let conversationLog = [];
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
const textarea = document.getElementById('briefingInput');
const charCount = document.getElementById('briefingCharCount');
const briefingBtn = document.getElementById('briefingBtn');
const saveBtn = document.getElementById('saveBtn');

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

  // 로딩 버블 — Malu 연구소장
  const loadingId = appendMsg('malu', '🌺 Malu 연구소장이 연구소 자료를 탐색하고 있습니다...', true);

  try {
    // 1차: Gateway API 시도 → /malu/briefing 또는 /aria/inquiry fallback
    const answer = await fetchBriefing(question, selectedTopic);
    removeMsg(loadingId);
    appendMsg('malu', answer);
  } catch {
    // 2차: 로컬 KB fallback
    removeMsg(loadingId);
    const fallback = localBriefing(question, selectedTopic);
    appendMsg('malu', fallback + '\n\n*— 현재 연구소 서버 연결 중, 로컬 브리핑으로 응답합니다.*');
  }

  briefingBtn.disabled = false;
  briefingBtn.textContent = '브리핑 요청 →';
  msgCount++;

  if (msgCount >= 3) saveBtn.style.display = 'inline-block';
});

/* ── MD 저장 ── */
saveBtn.addEventListener('click', () => {
  const md = generateMarkdown();
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mulberry-briefing-${new Date().toISOString().slice(0,10)}.md`;
  a.click();
  URL.revokeObjectURL(url);
});

/* ── Gateway API 호출 ── */
async function fetchBriefing(question, topic) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), API_TIMEOUT);
  try {
    // /malu/briefing 엔드포인트 우선 시도, 없으면 /aria/inquiry fallback
    let res = await fetch(`${GATEWAY_URL}/malu/briefing`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: question, category: topicToCategory(topic), role: 'briefing' }),
      signal: ctrl.signal,
    });

    // /malu/briefing 없으면 /aria/inquiry 시도
    if (!res.ok && res.status === 404) {
      res = await fetch(`${GATEWAY_URL}/aria/inquiry`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: question, category: topicToCategory(topic) }),
        signal: ctrl.signal,
      });
    }

    clearTimeout(timer);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const body = data?.response?.comment_body || data?.response || '';
    // 응답 본문 추출 (와룡 또는 Malu 섹션)
    const match = body.match(/(?:## 🌺 Malu|## 🐉 와룡)[\s\S]+?\n\n([\s\S]+?)(?:\n---|\*신뢰도|$)/);
    return match ? match[1].trim() : (typeof body === 'string' ? body : localBriefing(question, topic));
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
  const cls = role === 'user' ? 'user' : 'system';

  const div = document.createElement('div');
  div.className = `chat-msg ${cls}`;
  div.id = id;
  div.innerHTML = `
    <span class="chat-avatar">${avatar}</span>
    <div class="chat-bubble ${isLoading ? 'loading' : ''}">${markdownToHtml(text)}</div>
  `;
  history.appendChild(div);
  history.scrollTop = history.scrollHeight;

  if (!isLoading) conversationLog.push({ role, text, ts: new Date().toLocaleString('ko-KR') });
  return id;
}

function removeMsg(id) { document.getElementById(id)?.remove(); }

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
    `**브리핑 담당**: Malu 연구소장 🌺`,
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
      lines.push(`## 🌺 Malu 연구소장 브리핑`);
      lines.push(text);
    }
    lines.push('');
  });
  lines.push('---');
  lines.push('*Mulberry Research Lab · 장승배기 헌법 정신 기반 · 2026*');
  lines.push('*Briefing by Malu 연구소장 🌺*');
  return lines.join('\n');
}
