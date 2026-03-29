/**
 * Mulberry AI Rest Scheduler (MARRF)
 * 
 * AI 에이전트에게 휴식(rest)을 강제하는 스케줄러
 * - 작업-휴식 주기 기반
 * - 휴식 중 응답 품질 저하, Bio 메시지 변경 등과 연계 가능
 * 
 * @version 1.0
 * @author Mulberry Research Lab (re.eul)
 * @license MIT
 */

class RestScheduler {
  /**
   * @param {Object} agent - AI 에이전트 인스턴스 (execute, updateBio 등 메서드 보유)
   * @param {Object} policy - 휴식 정책
   * @param {string} policy.type - 'interval' | 'scheduled' | 'ourhome'
   * @param {number} policy.workDuration - 작업 시간 (분)
   * @param {number} policy.restDuration - 휴식 시간 (분)
   * @param {number} [policy.extraRestEvery=0] - N주기마다 추가 휴식 (분)
   */
  constructor(agent, policy) {
    this.agent = agent;
    this.policy = policy;
    this.isResting = false;
    this.workTimer = null;
    this.restTimer = null;
    this.cycleCount = 0;
    this.listeners = []; // 상태 변경 리스너

    // 정책 기본값
    this.policy.workDuration = policy.workDuration || 45;
    this.policy.restDuration = policy.restDuration || 5;
    this.policy.extraRestEvery = policy.extraRestEvery || 0;
    this.policy.extraRestDuration = policy.extraRestDuration || 15;
  }

  /**
   * 스케줄러 시작 (작업 모드 진입)
   */
  start() {
    if (this.workTimer) clearTimeout(this.workTimer);
    if (this.restTimer) clearTimeout(this.restTimer);
    this.isResting = false;
    this._scheduleWorkPeriod();
    console.log(`[RestScheduler] Started with policy: work ${this.policy.workDuration}min / rest ${this.policy.restDuration}min`);
  }

  /**
   * 작업 주기 스케줄링
   */
  _scheduleWorkPeriod() {
    this.workTimer = setTimeout(() => {
      this._startRest();
    }, this.policy.workDuration * 60 * 1000);
  }

  /**
   * 휴식 시작
   */
  _startRest() {
    this.isResting = true;
    this._notifyListeners('rest_start', { duration: this.policy.restDuration });
    
    // 에이전트에게 휴식 시작 알림 (Bio 변경, 응답 품질 조정 등)
    if (this.agent.onRestStart) {
      this.agent.onRestStart(this.policy.restDuration);
    }
    
    console.log(`[RestScheduler] Rest started for ${this.policy.restDuration} min`);
    
    this.restTimer = setTimeout(() => {
      this._endRest();
    }, this.policy.restDuration * 60 * 1000);
  }

  /**
   * 휴식 종료
   */
  _endRest() {
    this.isResting = false;
    this.cycleCount++;
    this._notifyListeners('rest_end', { cycle: this.cycleCount });
    
    if (this.agent.onRestEnd) {
      this.agent.onRestEnd();
    }
    
    console.log(`[RestScheduler] Rest ended. Cycle ${this.cycleCount} completed.`);
    
    // 추가 휴식 확인
    if (this.policy.extraRestEvery > 0 && this.cycleCount % this.policy.extraRestEvery === 0) {
      this._startExtraRest();
    } else {
      this._scheduleWorkPeriod();
    }
  }

  /**
   * 추가 휴식 (의무 휴식 정책용)
   */
  _startExtraRest() {
    this.isResting = true;
    this._notifyListeners('extra_rest_start', { duration: this.policy.extraRestDuration });
    
    if (this.agent.onRestStart) {
      this.agent.onRestStart(this.policy.extraRestDuration, true); // extra flag
    }
    
    console.log(`[RestScheduler] Extra rest started for ${this.policy.extraRestDuration} min`);
    
    this.restTimer = setTimeout(() => {
      this.isResting = false;
      if (this.agent.onRestEnd) this.agent.onRestEnd();
      this._scheduleWorkPeriod();
    }, this.policy.extraRestDuration * 60 * 1000);
  }

  /**
   * 현재 휴식 중인지 반환
   */
  getStatus() {
    return { isResting: this.isResting, cycle: this.cycleCount };
  }

  /**
   * 수동으로 휴식 시작 (운영자 개입)
   */
  forceRest(durationMinutes = 10) {
    if (this.workTimer) clearTimeout(this.workTimer);
    if (this.restTimer) clearTimeout(this.restTimer);
    this._startManualRest(durationMinutes);
  }

  _startManualRest(duration) {
    this.isResting = true;
    this._notifyListeners('manual_rest_start', { duration });
    if (this.agent.onRestStart) this.agent.onRestStart(duration, true);
    
    this.restTimer = setTimeout(() => {
      this.isResting = false;
      if (this.agent.onRestEnd) this.agent.onRestEnd();
      this._scheduleWorkPeriod();
    }, duration * 60 * 1000);
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

  /**
   * 스케줄러 중단
   */
  stop() {
    if (this.workTimer) clearTimeout(this.workTimer);
    if (this.restTimer) clearTimeout(this.restTimer);
    this.isResting = false;
    console.log('[RestScheduler] Stopped');
  }
}

// 간단한 테스트용 더미 에이전트 (실제 사용 시에는 Mulberry Agent 클래스로 대체)
class DummyAgent {
  onRestStart(duration, isExtra = false) {
    console.log(`[DummyAgent] Rest starting for ${duration} min${isExtra ? ' (extra)' : ''}`);
  }
  onRestEnd() {
    console.log('[DummyAgent] Rest ended, resuming work');
  }
}

// 모듈 내보내기 (Node.js)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { RestScheduler, DummyAgent };
}

// 실행 예시 (직접 테스트 시)
if (require.main === module) {
  const agent = new DummyAgent();
  const scheduler = new RestScheduler(agent, {
    type: 'interval',
    workDuration: 1,   // 테스트용 1분 작업
    restDuration: 0.5, // 테스트용 30초 휴식
    extraRestEvery: 2,
    extraRestDuration: 1
  });
  scheduler.start();
  // 5분 후 자동 종료 (예시)
  setTimeout(() => scheduler.stop(), 5 * 60 * 1000);
}
