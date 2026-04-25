/**
 * Project: Mulberry Research Lab (MRL)
 * Module: JIT(Just-In-Time) Auth Token Protocol
 * Purpose: Zero-Trust 기반 에이전트 실행 권한 일시 부여 및 즉시 파기
 */

const crypto = require('crypto');

class JITAuthProtocol {
    constructor(secretKey) {
        // 사령관님만이 보유한 마스터 키 (환경 변수 권장)
        this.masterSecret = secretKey || process.env.MRL_MASTER_SECRET;
        this.activeSession = null;
    }

    /**
     * 1단계: 에이전트 실행 직전 세션 토큰 생성 (유효기간 30초)
     */
    generateSessionToken(agentId) {
        const timestamp = Date.now();
        const payload = `${agentId}:${timestamp}`;
        const signature = crypto
            .createHmac('sha256', this.masterSecret)
            .update(payload)
            .digest('hex');

        this.activeSession = {
            token: Buffer.from(`${payload}:${signature}`).toString('base64'),
            expiresAt: timestamp + 30000 // 30초 후 만료
        };

        return this.activeSession.token;
    }

    /**
     * 2단계: 에이전트 내부에서 토큰 검증 및 실행 승인
     */
    verifyAndExecute(receivedToken, callback) {
        try {
            const decoded = Buffer.from(receivedToken, 'base64').toString('utf8');
            const [agentId, timestamp, signature] = decoded.split(':');

            // 검증 1: 유효 시간 확인 (Zero-Trust)
            if (Date.now() > parseInt(timestamp) + 30000) {
                throw new Error("MRL_SECURITY_ERROR: Token Expired");
            }

            // 검증 2: 서명 무결성 확인
            const expectedSignature = crypto
                .createHmac('sha256', this.masterSecret)
                .update(`${agentId}:${timestamp}`)
                .digest('hex');

            if (signature !== expectedSignature) {
                throw new Error("MRL_SECURITY_ERROR: Unauthorized Signature");
            }

            // 검증 완료 후 즉시 실행 및 세션 파기
            console.log(`[MRL-SYSTEM] Agent ${agentId} Verified. Executing...`);
            callback();
            
            // 3단계: 권한 즉시 파기 (Least Privilege)
            this.activeSession = null;

        } catch (error) {
            console.error(`[MRL-ALARM] Security Breach Attempt: ${error.message}`);
            return false;
        }
    }
}

module.exports = JITAuthProtocol;
