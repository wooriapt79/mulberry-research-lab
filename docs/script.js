// Mulberry Aria Portal · v1.0
// GitHub Issues 연동 (Pre-filled URL 리디렉션 방식)
const REPO = 'wooriapt79/mulberry-research-lab';

document.getElementById('sendBtn').addEventListener('click', () => {
  const input = document.getElementById('userInput');
  const status = document.getElementById('status');
  const msg = input.value.trim();

  if (!msg) {
    status.textContent = '⚠️ 메시지를 입력해주세요.';
    return;
  }

  status.textContent = ' 기록창으로 전송 중...';
  const title = encodeURIComponent(`[Aria Guide] ${msg.slice(0, 50)}${msg.length > 50 ? '...' : ''}`);
  const body = encodeURIComponent(`**방문객 메시지**\n${msg}\n\n---\n*전송 시각: ${new Date().toLocaleString()}*`);
  const issueUrl = `https://github.com/${REPO}/issues/new?title=${title}&body=${body}&labels=aria-guide`;

  window.open(issueUrl, '_blank');
  status.textContent = '✅ Issue 가 열렸습니다. 제출 시 Pulse Daemon 이 감지하여 Aria 가 자동 응답합니다.';
  input.value = '';
});