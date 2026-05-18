// Mulberry Research Lab · Aria Portal · script.js v2.0
// RyuWon 소환 에디션 — GitHub Issues 연동 (Pre-filled URL + Popup Fallback)

const REPO   = 'wooriapt79/mulberry-research-lab';
const AGENT  = '와룡 (臥龍)';  // 소환된 에이전트 — 대화·추론
const MAX_LEN = 500;

/* ─── 상태 ─── */
let selectedCategory = '일반 문의';

/* ─── 카테고리 버튼 ─── */
document.querySelectorAll('.cat-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedCategory = btn.dataset.cat;
  });
});

/* ─── 글자 수 카운터 ─── */
const textarea   = document.getElementById('userInput');
const charCount  = document.getElementById('charCount');
const sendBtn    = document.getElementById('sendBtn');

textarea.addEventListener('input', () => {
  const len = textarea.value.length;
  charCount.textContent = `${len} / ${MAX_LEN}`;
  charCount.classList.remove('warn', 'over');
  if (len >= MAX_LEN) {
    charCount.classList.add('over');
    sendBtn.disabled = true;
  } else if (len >= MAX_LEN * 0.8) {
    charCount.classList.add('warn');
    sendBtn.disabled = false;
  } else {
    sendBtn.disabled = false;
  }
});

/* ─── 전송 ─── */
sendBtn.addEventListener('click', () => {
  const msg = textarea.value.trim();
  const statusArea   = document.getElementById('statusArea');
  const fallbackArea = document.getElementById('fallbackArea');
  const fallbackLink = document.getElementById('fallbackLink');

  // 초기화
  statusArea.style.display   = 'none';
  statusArea.classList.remove('error');
  fallbackArea.style.display = 'none';

  if (!msg) {
    showStatus('⚠️ 메시지를 입력해주세요.', true);
    return;
  }

  // GitHub Issue 제목 / 본문 구성
  const shortMsg = msg.length > 50 ? msg.slice(0, 50) + '...' : msg;
  const title = `[Aria · ${selectedCategory}] ${shortMsg}`;
  const body = [
    `**카테고리**: ${selectedCategory}`,
    `**소환 에이전트**: ${AGENT} 🌊`,
    ``,
    `**방문객 메시지**`,
    msg,
    ``,
    `---`,
    `*전송 시각: ${new Date().toLocaleString('ko-KR')}*`,
    `*Aria Portal v2.0 · mulberry-research-lab*`
  ].join('\n');

  const issueUrl = buildIssueUrl(title, body);
  fallbackLink.href = issueUrl;

  // 전송 시도
  sendBtn.disabled = true;
  sendBtn.textContent = '전송 중...';

  const popup = window.open(issueUrl, '_blank');

  setTimeout(() => {
    sendBtn.disabled = false;
    sendBtn.textContent = '전송 →';

    if (!popup || popup.closed || typeof popup.closed === 'undefined') {
      // 팝업 차단됨
      showStatus('⚠️ 팝업이 차단되었습니다. 아래 링크를 직접 클릭하세요.', true);
      fallbackArea.style.display = 'block';
    } else {
      // 성공
      showStatus(`✅ ${AGENT}이 메시지를 받았습니다. GitHub Issue가 열렸습니다.\n팀이 확인 후 직접 답변드립니다.`);
      textarea.value = '';
      charCount.textContent = `0 / ${MAX_LEN}`;
    }
  }, 400);
});

/* ─── 엔터키 전송 (Shift+Enter = 줄바꿈) ─── */
textarea.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendBtn.click();
  }
});

/* ─── 헬퍼 ─── */
function buildIssueUrl(title, body) {
  const base = `https://github.com/${REPO}/issues/new`;
  const params = new URLSearchParams({
    title,
    body,
    labels: 'aria-guide'
  });
  return `${base}?${params.toString()}`;
}

function showStatus(msg, isError = false) {
  const statusArea = document.getElementById('statusArea');
  statusArea.textContent = msg;
  statusArea.style.display = 'block';
  if (isError) {
    statusArea.classList.add('error');
  } else {
    statusArea.classList.remove('error');
  }
}

/* ─── 와룡 featured 카드 강조 ─── */
document.querySelectorAll('.agent-card').forEach(card => {
  const name = card.querySelector('.agent-name');
  if (name && name.textContent.trim() === '와룡') {
    card.classList.add('featured');
  }
});
