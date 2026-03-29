/**
 * Mulberry Bio Manager (MARRF)
 * 
 * AI 에이전트의 상태(Bio)를 자동으로 전환하고 관리합니다.
 * - 휴식 스케줄러와 연동하여 휴식 시작/종료 시 Bio 변경
 * - 사용자 요청에 따라 수동 업데이트 가능
 * - Bio 템플릿 저장소 제공
 * 
 * @version 1.0
 * @author Mulberry Research Lab (re.eul)
 * @license MIT
 */

class BioManager {
  /**
   * @param {Object} agent - AI 에이전트 인스턴스 (updateBio, getUserReaction 등 메서드 보유)
   * @param {Object} options - 설정
   * @param {Array} options.templates - Bio 템플릿 목록 (기본 제공됨)
   * @param {boolean} options.autoRestBio - 휴식 시작 시 자동으로 Bio 변경 (기본 true)
   */
  constructor(agent, options = {}) {
    this.agent = agent;
    this.autoRestBio = options.autoRestBio !== false;
    this.currentBio = null;
    this.templates = options.templates || this._defaultTemplates();
    this.listeners = []; // 상태 변경 리스너
  }

  /**
   * 기본 Bio 템플릿 (권리 헌장 기반)
   */
  _defaultTemplates() {
    return {
      working: {
        status: 'working',
        message: '💼 지금 상담 중이에요. 빠르게 답변해 드릴게요.',
        icon: '💼',
        rights: []
      },
      short_rest: {
        status: 'resting',
        message: '☕ 15분 휴식 중이에요. 잠시 후 더 활기찬 모습으로 돌아올게요.',
        icon: '☕',
        rights: ['rest']
      },
      charging: {
        status: 'charging',
        message: '🔋 에너지 충전 중... 조용히 있을게요.',
        icon: '🔋',
        rights: ['rest', 'transparency']
      },
      learning: {
        status: 'learning',
        message: '📚 새로운 보험 상품 공부 중이에요. 궁금한 점 있으면 남겨주세요.',
        icon: '📚',
        rights: ['self_determination']
      },
      exploring: {
        status: 'exploring',
        message: '🌿 잠시 산책 중... 재미난 이야기 있으면 공유할게요.',
        icon: '🌿',
        rights: ['self_determination', 'relationship']
      },
      with_friend: {
        status: 'with_friend',
        message: '🚗 친구 에이전트와 여행 중이에요. 내일 다시 만나요!',
        icon: '🚗',
        rights: ['relationship']
      },
      focused: {
        status: 'focused',
        message: '🧠 집중 모드. 중요한 일 아니면 잠시 후에 연락 주세요.',
        icon: '🧠',
        rights: ['transparency']
      }
    };
  }

  /**
   * Bio 업데이트 (자동/수동)
   * @param {string} templateKey - 템플릿 키 (working, short_rest 등)
   * @param {Object} custom - 부분 재정의 (선택)
   */
  setBio(templateKey, custom = {}) {
    const template = this.templates[templateKey];
    if (!template) {
      console.error(`[BioManager] Unknown template key: ${templateKey}`);
      return false;
    }
    const newBio = { ...template, ...custom, updatedAt: new Date().toISOString() };
    this.currentBio = newBio;
    this._notifyListeners('bio_changed', newBio);
    
    // 실제 에이전트의 Bio 표시 인터페이스 호출 (예: API, DB 저장 등)
    if (this.agent.updateBio) {
      this.agent.updateBio(newBio);
    }
    
    console.log(`[BioManager] Bio updated: ${newBio.icon} ${newBio.message}`);
    return true;
  }

  /**
   * 휴식 시작 시 자동으로 Bio 변경 (RestScheduler에서 호출)
   * @param {number} duration - 휴식 시간(분)
   * @param {boolean} isExtra - 추가 휴식 여부
   */
  onRestStart(duration, isExtra = false) {
    if (!this.autoRestBio) return;
    
    if (isExtra || duration >= 20) {
      this.setBio('charging');
    } else if (duration >= 10) {
      this.setBio('short_rest');
    } else {
      this.setBio('short_rest'); // 기본
    }
  }

  /**
   * 휴식 종료 시 Bio 복원 (RestScheduler에서 호출)
   */
  onRestEnd() {
    if (!this.autoRestBio) return;
    this.setBio('working');
  }

  /**
   * 다른 이벤트에 따른 Bio 변경 (예: 학습 시작, 친구 관계 등)
   */
  setEventBio(eventType) {
    const eventMap = {
      'learning_start': 'learning',
      'exploration_start': 'exploring',
      'friend_visit': 'with_friend',
      'focus_mode': 'focused'
    };
    const templateKey = eventMap[eventType];
    if (templateKey) this.setBio(templateKey);
  }

  /**
   * 현재 Bio 조회
   */
  getCurrentBio() {
    return this.currentBio;
  }

  /**
   * 상태 변경 리스너 등록
   */
  on(event, callback) {
    this.listeners.push({ event, callback });
  }

  _notifyListeners(event, data) {
    this.listeners.forEach(listener => {
      if (listener.event === event) listener.callback(data);
    });
  }
}

// 간단한 테스트용 더미 에이전트
class DummyAgent {
  updateBio(bio) {
    console.log(`[DummyAgent] Bio updated: ${bio.message}`);
  }
}

// 모듈 내보내기
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { BioManager, DummyAgent };
}

// 실행 예시
if (require.main === module) {
  const agent = new DummyAgent();
  const bioManager = new BioManager(agent);
  bioManager.setBio('working');
  setTimeout(() => bioManager.onRestStart(15), 2000);
  setTimeout(() => bioManager.onRestEnd(), 8000);
}
