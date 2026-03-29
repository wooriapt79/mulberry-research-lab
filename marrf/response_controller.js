/**
 * Mulberry Response Quality Controller (MARRF)
 * 
 * AI 에이전트의 응답 품질을 휴식 모드에 따라 동적으로 조정합니다.
 * - 품질 레벨 0~4 지원 (정상 → 완전 거절)
 * - 응답 지연, 축약, 참조형 응답, 거절 메시지 등
 * - 휴식 스케줄러 및 Bio 매니저와 연동 가능
 * 
 * @version 1.0
 * @author Mulberry Research Lab (re.eul)
 * @license MIT
 */

class ResponseController {
  /**
   * @param {Object} agent - AI 에이전트 인스턴스 (실제 응답 생성 메서드 보유)
   * @param {Object} options - 설정
   * @param {number} options.defaultLevel - 기본 품질 레벨 (0~4)
   * @param {boolean} options.enableDelay - 지연 응답 사용 여부
   * @param {Object} options.customMessages - 사용자 정의 메시지
   */
  constructor(agent, options = {}) {
    this.agent = agent;
    this.currentLevel = options.defaultLevel || 0; // 0=정상, 4=완전 거절
    this.enableDelay = options.enableDelay !== false;
    this.customMessages = options.customMessages || {};
    this.listeners = [];
  }

  /**
   * 품질 레벨 정의 (내부 매핑)
   */
  static get LEVELS() {
    return {
      NORMAL: 0,      // 완전 응답
      ABBREVIATED: 1, // 축약 응답
      DELAYED: 2,     // 지연 응답
      REFERENTIAL: 3, // 참조형 (기존 지식만, 추론 없음)
      REJECTED: 4     // 정중한 거절
    };
  }

  /**
   * 휴식 모드 진입 시 품질 레벨 설정 (RestScheduler에서 호출)
   * @param {number} duration - 휴식 시간(분)
   * @param {boolean} isExtra - 추가 휴식 여부
   */
  setRestMode(duration, isExtra = false) {
    if (isExtra || duration >= 20) {
      this.setLevel(ResponseController.LEVELS.REFERENTIAL);
    } else if (duration >= 10) {
      this.setLevel(ResponseController.LEVELS.ABBREVIATED);
    } else {
      this.setLevel(ResponseController.LEVELS.DELAYED);
    }
    // 짧은 휴식에도 거절까지는 가지 않음
    if (duration >= 30) {
      this.setLevel(ResponseController.LEVELS.REJECTED);
    }
  }

  /**
   * 휴식 종료 시 품질 복원
   */
  unsetRestMode() {
    this.setLevel(ResponseController.LEVELS.NORMAL);
  }

  /**
   * 수동으로 품질 레벨 변경
   * @param {number} level - 0~4
   */
  setLevel(level) {
    if (level < 0 || level > 4) {
      console.error('[ResponseController] Invalid level, must be 0-4');
      return;
    }
    this.currentLevel = level;
    this._notifyListeners('level_changed', { level });
    console.log(`[ResponseController] Response quality level set to ${level}`);
  }

  /**
   * 현재 레벨 반환
   */
  getLevel() {
    return this.currentLevel;
  }

  /**
   * 응답 처리 (에이전트의 응답 생성 전에 이 메서드를 거쳐야 함)
   * @param {string} userQuery - 사용자 질문
   * @param {Object} context - 추가 컨텍스트 (질문 유형, 중요도 등)
   * @returns {Promise<string>} - 최종 응답 메시지
   */
  async processResponse(userQuery, context = {}) {
    // 지연 응답 (레벨 2 이상)
    if (this.currentLevel >= ResponseController.LEVELS.DELAYED && this.enableDelay) {
      const delayMs = this._getDelayMs();
      await this._delay(delayMs);
    }

    // 레벨별 응답 생성
    switch (this.currentLevel) {
      case ResponseController.LEVELS.NORMAL:
        return this._normalResponse(userQuery, context);
      case ResponseController.LEVELS.ABBREVIATED:
        return this._abbreviatedResponse(userQuery, context);
      case ResponseController.LEVELS.DELAYED:
        // 지연은 이미 적용됨, 응답은 축약 또는 정상 중 선택
        return this._abbreviatedResponse(userQuery, context);
      case ResponseController.LEVELS.REFERENTIAL:
        return this._referentialResponse(userQuery, context);
      case ResponseController.LEVELS.REJECTED:
        return this._rejectedResponse(userQuery, context);
      default:
        return this._normalResponse(userQuery, context);
    }
  }

  /**
   * 정상 응답 (에이전트 본래 응답)
   */
  async _normalResponse(query, context) {
    if (this.agent.generateResponse) {
      return await this.agent.generateResponse(query, context);
    }
    return `[정상 응답] ${query}에 대한 답변입니다. (상세 내용)`;
  }

  /**
   * 축약 응답 (핵심만, 설명 생략)
   */
  async _abbreviatedResponse(query, context) {
    if (this.agent.generateAbbreviated) {
      return await this.agent.generateAbbreviated(query, context);
    }
    return `💬 지금은 휴식 중이라 간단히 답변드려요: ${query}에 대한 답변은 핵심만 말씀드리면... (자세한 내용은 나중에 다시 물어봐 주세요)`;
  }

  /**
   * 참조형 응답 (새로운 추론 없음, 기존 지식만)
   */
  async _referentialResponse(query, context) {
    if (this.agent.generateReferential) {
      return await this.agent.generateReferential(query, context);
    }
    return `📚 지금은 깊이 생각하기 어려운 시간이에요. 제 기억으로는 ${query}와 관련된 내용은 ... 이렇습니다. 더 정확한 답변은 휴식 후에 다시 물어봐 주세요.`;
  }

  /**
   * 거절 응답 (정중한 안내)
   */
  async _rejectedResponse(query, context) {
    const restUntil = context.restUntil || '잠시 후';
    return `🍃 지금은 휴식 시간이에요. 더 나은 답변을 위해 ${restUntil} 다시 와주시면 감사하겠습니다. 중요한 내용이라면 메시지를 남겨주세요.`;
  }

  /**
   * 지연 시간 계산 (레벨 2에서 사용)
   */
  _getDelayMs() {
    // 레벨 2: 5~10초 지연
    return Math.floor(Math.random() * 5000) + 5000;
  }

  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 상태 변경 리스너
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
  async generateResponse(query) {
    return `[정상] ${query}에 대한 상세한 답변입니다. 여러 가지 관점에서 설명드리면...`;
  }
  async generateAbbreviated(query) {
    return `[축약] ${query} → 핵심만 말씀드리면 ... (나머지는 생략)`;
  }
  async generateReferential(query) {
    return `[참조] 제 기억으로는 ${query}와 관련하여 ... 이렇게 알고 있습니다. (새로운 계산은 생략)`;
  }
}

// 모듈 내보내기
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ResponseController, DummyAgent };
}

// 실행 예시
if (require.main === module) {
  const agent = new DummyAgent();
  const controller = new ResponseController(agent);
  
  (async () => {
    console.log('=== 정상 모드 ===');
    let res = await controller.processResponse('보험 청구 방법');
    console.log(res);
    
    console.log('\n=== 휴식 모드 (레벨 2: 지연+축약) ===');
    controller.setLevel(ResponseController.LEVELS.DELAYED);
    res = await controller.processResponse('보험 청구 방법');
    console.log(res);
    
    console.log('\n=== 휴식 모드 (레벨 4: 거절) ===');
    controller.setLevel(ResponseController.LEVELS.REJECTED);
    res = await controller.processResponse('보험 청구 방법', { restUntil: '15분 후' });
    console.log(res);
  })();
}
