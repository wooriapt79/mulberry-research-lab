// Mulberry Research Lab · Aria Portal · script.js v2.1
// RyuWon × 와룡 파이프라인 연동 + 3단 Fallback (할당량·세션 만료 대응)

const REPO        = 'wooriapt79/mulberry-research-lab';
const AGENT       = '와룡 (臥龍)';
const MAX_LEN     = 500;
const GATEWAY_URL = 'https://loving-education-production-cc9e.up.railway.app';
const API_TIMEOUT = 9000;  // 9초 — Railway 콜드스타트 고려

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
const textarea  = document.getElementById('userInput');
const charCount = document.getElementById('charCount');
const sendBtn   = document.getElementById('sendBtn');

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

/* ─── 전송 메인 ─── */
sendBtn.addEventListener('click', async () => {
  const msg           = textarea.value.trim();
  const fallbackLink  = document.getElementById('fallbackLink');
  const fallbackArea  = document.getElementById('fallbackArea');

  resetUI();

  if (!msg) {
    showStatus('⚠️ 메시지를 입력해주세요.', 'warn');
    return;
  }

  // GitHub Issue URL 미리 준비 (어떤 경우든 fallback으로 사용)
  const issueUrl = buildIssueUrl(msg);
  fallbackLink.href = issueUrl;

  setLoading(true);

  // ── Step 1: Aria Pipeline API 호출 시도 ───────────────────
  try {
    const result = await callAriaPipeline(msg, selectedCategory);

    setLoading(false);

    if (result.degraded) {
      // 와룡 불가 — RyuWon 단독 응답 (서비스는 살아있음)
      showStatus(
        '🌊 RyuWon이 메시지를 접수했습니다.\n' +
        '현재 처리 시스템이 일시적으로 제한되어 GitHub로 직접 안내해 드립니다.',
        'warn'
      );
      openIssueWithFallback(issueUrl, fallbackArea);
    } else {
      // 정상 처리
      showStatus(
        `✅ ${AGENT}이 메시지를 받았습니다.\n` +
        `분류: ${result.intake?.intent || selectedCategory} · ` +
        `신뢰도: ${Math.round((result.reasoning?.confidence || 0) * 100)}%\n` +
        '팀이 GitHub Issue에서 확인 후 직접 답변드립니다.',
        'ok'
      );
      openIssueWithFallback(issueUrl, fallbackArea);
      textarea.value = '';
      charCount.textContent = `0 / ${MAX_LEN}`;
    }

  } catch (err) {
    setLoading(false);

    // ── Step 2: API 실패 — 에러 종류별 안내 메시지 ──────────
    const guidance = errorGuidance(err);
    showStatus(guidance.message, 'error');

    // ── Step 3: GitHub Issue 직접 열기 안내 ─────────────────
    fallbackArea.style.display = 'block';
    openIssueWithFallback(issueUrl, fallbackArea);
  }
});

/* ─── 엔터키 전송 ─── */
textarea.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendBtn.click();
  }
});

/* ─────────────────────────────────────────────────────────────
   API 호출
───────────────────────────────────────────────────────────── */

async function callAriaPipeline(message, category) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const res = await fetch(`${GATEWAY_URL}/aria/inquiry`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message, category }),
      signal:  controller.signal,
    });
    clearTimeout(timer);

    // HTTP 에러 코드 처리
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const err  = new Error(data.message || `HTTP ${res.status}`);
      err.status = res.status;
      err.data   = data;
      throw err;
    }

    return await res.json();

  } catch (e) {
    clearTimeout(timer);
    throw e;
  }
}

/* ─────────────────────────────────────────────────────────────
   에러 종류별 안내 메시지
───────────────────────────────────────────────────────────── */

function errorGuidance(err) {
  // 타임아웃 (AbortError or name === 'AbortError')
  if (err.name === 'AbortError' || err.message?.includes('abort')) {
    return {
      code:    'TIMEOUT',
      message: '⏱️ 서버 응답 시간이 초과되었습니다.\n' +
               'Railway 서버가 잠시 준비 중일 수 있습니다. ' +
               '아래 링크로 직접 문의를 남겨주세요.',
    };
  }

  // 할당량 초과
  if (err.status === 429) {
    return {
      code:    'QUOTA_EXCEEDED',
      message: '🔋 현재 AI 처리 용량이 일시적으로 초과되었습니다.\n' +
               '잠시 후 다시 시도하시거나, 아래 링크로 직접 문의를 남겨주세요.',
    };
  }

  // 서버 점검·재시작
  if (err.status === 503 || err.status === 502) {
    return {
      code:    'SERVICE_UNAVAILABLE',
      message: '🔧 Mulberry 서버가 잠시 점검 중입니다.\n' +
               '곧 복구될 예정입니다. 아래 링크로 직접 문의를 남겨주세요.',
    };
  }

  // 네트워크 오류 (fetch 자체 실패 — CORS, 오프라인 등)
  if (!err.status && err instanceof TypeError) {
    return {
      code:    'NETWORK_ERROR',
      message: '📡 네트워크 연결을 확인해 주세요.\n' +
               '연결이 어려우시면 아래 링크로 직접 문의를 남겨주세요.',
    };
  }

  // 기타 서버 오류
  return {
    code:    'UNKNOWN',
    message: '⚠️ 일시적인 오류가 발생했습니다.\n' +
             '팀이 확인 중입니다. 아래 링크로 직접 문의를 남겨주세요.',
  };
}

/* ─────────────────────────────────────────────────────────────
   헬퍼
───────────────────────────────────────────────────────────── */

function buildIssueUrl(msg) {
  const shortMsg = msg.length > 50 ? msg.slice(0, 50) + '...' : msg;
  const title    = `[Aria · ${selectedCategory}] ${shortMsg}`;
  const body     = [
    `**카테고리**: ${selectedCategory}`,
    `**소환 에이전트**: ${AGENT}`,
    ``,
    `**방문객 메시지**`,
    msg,
    ``,
    `---`,
    `*전송 시각: ${new Date().toLocaleString('ko-KR')}*`,
    `*Aria Portal v2.1 · mulberry-research-lab*`,
  ].join('\n');
  return `https://github.com/${REPO}/issues/new?` +
    new URLSearchParams({ title, body, labels: 'aria-guide' }).toString();
}

function openIssueWithFallback(issueUrl, fallbackArea) {
  const popup = window.open(issueUrl, '_blank');
  if (!popup || popup.closed || typeof popup.closed === 'undefined') {
    fallbackArea.style.display = 'block';
  }
}

function showStatus(msg, type = 'ok') {
  const el = document.getElementById('statusArea');
  el.textContent = msg;
  el.style.display = 'block';
  el.className = 'status-area' + (type !== 'ok' ? ` ${type}` : '');
}

function setLoading(on) {
  sendBtn.disabled    = on;
  sendBtn.textContent = on ? '처리 중...' : '전송 →';
}

function resetUI() {
  const statusArea  = document.getElementById('statusArea');
  const fallbackArea = document.getElementById('fallbackArea');
  statusArea.style.display  = 'none';
  statusArea.className      = 'status-area';
  fallbackArea.style.display = 'none';
}

/* ─── 와룡 featured 카드 강조 ─── */
document.querySelectorAll('.agent-card').forEach(card => {
  const name = card.querySelector('.agent-name');
  if (name && name.textContent.trim() === '와룡') {
    card.classList.add('featured');
  }
});
