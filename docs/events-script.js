// Mulberry Events Script — 카카오 채널 연동
// 채널 홈: http://pf.kakao.com/_xmVxmMC
// 채팅 URL: http://pf.kakao.com/_xmVxmMC/chat

const KAKAO_CHANNEL = 'http://pf.kakao.com/_xmVxmMC';
const KAKAO_CHAT    = 'http://pf.kakao.com/_xmVxmMC/chat';

// 카카오 채팅 열기 (Luna 문의)
function contactLuna() {
  window.open(KAKAO_CHAT, '_blank', 'noopener,noreferrer');
}

// 이벤트 참여 신청 → 카카오 채팅
function participateEvent(eventName) {
  window.open(KAKAO_CHAT, '_blank', 'noopener,noreferrer');
}

// 자세히 보기 → 카카오 채팅
function viewDetails(topic) {
  window.open(KAKAO_CHAT, '_blank', 'noopener,noreferrer');
}

// 커뮤니티 참여 → 카카오 채팅
function joinCommunity() {
  window.open(KAKAO_CHAT, '_blank', 'noopener,noreferrer');
}

// 더 알아보기 → 카카오 채널 홈
function learnMore() {
  window.open(KAKAO_CHANNEL, '_blank', 'noopener,noreferrer');
}

// 공유하기
function shareEvent() {
  if (navigator.share) {
    navigator.share({ title: 'Mulberry 이벤트', url: location.href });
  } else {
    navigator.clipboard.writeText(location.href).then(() => {
      alert('링크가 복사되었습니다');
    });
  }
}
