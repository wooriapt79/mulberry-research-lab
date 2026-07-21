// ============================================
// FILTER FUNCTIONALITY
// ============================================

document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        // Remove active class from all buttons
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        // Add active class to clicked button
        this.classList.add('active');

        // Filter events
        const filter = this.getAttribute('data-filter');
        const events = document.querySelectorAll('.event-card');

        events.forEach(event => {
            if (filter === 'all' || event.getAttribute('data-category') === filter) {
                event.style.display = 'block';
                setTimeout(() => {
                    event.style.opacity = '1';
                }, 10);
            } else {
                event.style.display = 'none';
            }
        });
    });
});

// ============================================
// EVENT FUNCTIONS
// ============================================

function participateEvent(eventName) {
    alert(`${eventName} 이벤트에 참여하려면 Kakao 채널로 이동합니다.\n\n준비 중입니다!`);
    // TODO: Kakao 채널 링크로 연동
    // window.open('https://kakao-kuna-link', '_blank');
}

function viewDetails(eventName) {
    alert(`${eventName} 상세 정보 페이지로 이동합니다.\n\n준비 중입니다!`);
    // TODO: 상세 페이지 구현
}

function shareEvent(eventName) {
    const text = `Mulberry의 "${eventName}" 이벤트에 참여해보세요! 🌱\n\n식품사막화 제로 프로젝트 — Luna와 함께`;

    if (navigator.share) {
        navigator.share({
            title: 'Mulberry Event',
            text: text,
            url: window.location.href
        });
    } else {
        // Fallback: 클립보드에 복사
        navigator.clipboard.writeText(text);
        alert('공유 텍스트가 복사되었습니다!');
    }
}

function joinCommunity() {
    alert('커뮤니티에 참여하려면 Kakao 채널 또는 Naver 카페로 이동합니다.\n\n준비 중입니다!');
    // TODO: 커뮤니티 링크 연동
}

function contactLuna() {
    alert('Kakao Kuna 채널에서 Luna와 대화할 수 있습니다.\n\n준비 중입니다!');
    // TODO: Kakao 채널 링크
    // window.open('https://kakao-kuna-link', '_blank');
}

function learnMore() {
    alert('자세한 정보 페이지로 이동합니다.\n\n준비 중입니다!');
    // TODO: 정보 페이지 링크
}

// ============================================
// 실시간 카운트다운 (향후 구현)
// ============================================

function updateCountdown() {
    // 각 이벤트의 D-day 업데이트
    // 예: D-5 → D-4 (매일 자정에 업데이트)
}

// ============================================
// 로드 시 초기화
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🌱 Events section loaded!');
    console.log('Luna Events Platform v1.0');
    // 초기화 로직
});
