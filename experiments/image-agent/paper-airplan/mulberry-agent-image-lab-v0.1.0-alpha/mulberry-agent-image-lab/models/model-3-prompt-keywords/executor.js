/**
 * Mulberry Agent Image Lab - Model 3: Prompt Keywords
 * Agent Parser and Executor
 * 
 * 이미지 메타데이터에서 프롬프트 추출 → 키워드 파싱 → Agent 실행
 * 
 * @author CTO Koda
 * @date 2026-04-19
 * @version 1.0
 */

const fs = require('fs');
const { PNG } = require('pngjs');

// ==================== Agent 함수 사전 ====================

const AGENT_FUNCTIONS = {
  // AI/사고 관련
  'THINKEIN': function(context) {
    console.log('🧠 THINKEIN: AI Engine activated');
    context.aiMode = 'active';
    return { status: 'thinking', mode: 'active' };
  },
  
  // 데이터 처리
  'PROZESSING': function(context) {
    console.log('⚙️ PROZESSING: Data processing started');
    context.processing = true;
    return { status: 'processing', data: context.data };
  },
  
  // 라우팅/네트워크
  'ROUTIICG': function(context) {
    console.log('🔀 ROUTIICG: Setting up routing');
    const target = context.target || 'default';
    context.route = target;
    return { route: target, status: 'configured' };
  },
  
  // 서버 연결
  'ASTROFEN': function(context) {
    console.log('🌟 ASTROFEN: Connecting to celestial network');
    context.server = 'astro.mulberry.com';
    return { server: context.server, connected: true };
  },
  
  // GitHub 자동 설정
  'GITHUB_AUTOSETUP': function(context) {
    console.log('📦 GITHUB_AUTOSETUP: Setting up GitHub repository');
    // GitHub CLI 명령 실행
    const repoName = context.repo || 'mulberry-project';
    console.log(`  → Creating repository: ${repoName}`);
    return { repo: repoName, status: 'created' };
  },
  
  // Railway 배포
  'RAILWAY_DEPLOY': function(context) {
    console.log('🚂 RAILWAY_DEPLOY: Deploying to Railway');
    const service = context.service || 'mulberry-service';
    console.log(`  → Deploying service: ${service}`);
    return { service: service, status: 'deployed' };
  },
  
  // 워크벤치 설정
  'WORKBENCH_SETUP': function(context) {
    console.log('💻 WORKBENCH_SETUP: Setting up development environment');
    const ide = context.ide || 'vscode';
    console.log(`  → Configuring IDE: ${ide}`);
    return { ide: ide, status: 'configured' };
  },
  
  // 서버 엔드포인트
  'SERVELL': function(context) {
    console.log('📡 SERVELL: Server endpoint configured');
    const endpoint = context.endpoint || 'api.mulberry.com';
    context.endpoint = endpoint;
    return { endpoint: endpoint };
  },
  
  // 진입점
  'POE': function(context) {
    console.log('📊 POE: Point of Entry activated');
    return { entry: 'active' };
  },
  
  // 유지보수
  'MAIHESSHONE': function(context) {
    console.log('🔧 MAIHESSHONE: Maintenance mode');
    context.maintenance = true;
    return { mode: 'maintenance' };
  },
  
  // 병렬 처리
  'PROCEGANG': function(context) {
    console.log('⚡ PROCEGANG: Parallel processing enabled');
    context.parallel = true;
    return { workers: 'parallel', status: 'active' };
  }
};


// ==================== Agent Parser ====================

class AgentPromptParser {
  constructor() {
    this.functions = AGENT_FUNCTIONS;
  }
  
  /**
   * PNG 이미지에서 메타데이터 추출
   */
  extractMetadata(imagePath) {
    return new Promise((resolve, reject) => {
      const stream = fs.createReadStream(imagePath);
      const png = new PNG();
      
      stream.pipe(png);
      
      png.on('metadata', (metadata) => {
        resolve(metadata);
      });
      
      png.on('error', (err) => {
        reject(err);
      });
      
      // PNG 파싱
      png.on('parsed', () => {
        // text chunks 추출
        const textChunks = {};
        
        if (png.text) {
          for (const key in png.text) {
            textChunks[key] = png.text[key];
          }
        }
        
        resolve(textChunks);
      });
    });
  }
  
  /**
   * 프롬프트에서 Agent 키워드 파싱
   */
  parsePrompt(prompt) {
    const foundKeywords = [];
    
    // 모든 함수 키워드 찾기
    for (const keyword of Object.keys(this.functions)) {
      const regex = new RegExp(keyword, 'gi');
      const matches = [...prompt.matchAll(regex)];
      
      for (const match of matches) {
        foundKeywords.push({
          keyword: keyword,
          position: match.index,
          function: this.functions[keyword]
        });
      }
    }
    
    // 위치 순서대로 정렬
    foundKeywords.sort((a, b) => a.position - b.position);
    
    return foundKeywords;
  }
}


// ==================== Agent Executor ====================

class AgentExecutor {
  constructor() {
    this.parser = new AgentPromptParser();
    this.context = {};
  }
  
  /**
   * 이미지 파일에서 Agent 추출 및 실행
   */
  async executeFromImage(imagePath) {
    console.log('🖼️  Loading Agent Image...');
    console.log(`📁 File: ${imagePath}\n`);
    
    try {
      // 1. 메타데이터 추출
      const metadata = await this.parser.extractMetadata(imagePath);
      
      // 2. Agent 정보 확인
      const agentType = metadata.agent_type;
      const agentConfig = metadata.agent_config ? JSON.parse(metadata.agent_config) : null;
      const prompt = metadata.prompt;
      
      if (!prompt) {
        console.warn('⚠️  No prompt found in image metadata');
        return null;
      }
      
      console.log('✅ Agent detected!');
      console.log(`📋 Agent Type: ${agentType}`);
      console.log(`📝 Prompt: ${prompt.substring(0, 100)}...\n`);
      
      // 3. 프롬프트에서 키워드 파싱
      const keywords = this.parser.parsePrompt(prompt);
      
      if (keywords.length === 0) {
        console.warn('⚠️  No agent keywords found in prompt');
        return null;
      }
      
      console.log(`🔍 Found ${keywords.length} function keywords:\n`);
      keywords.forEach((k, i) => {
        console.log(`  ${i + 1}. ${k.keyword}`);
      });
      
      // 4. Context 설정
      if (agentConfig) {
        this.context = {
          ...this.context,
          ...agentConfig,
          type: agentType
        };
      }
      
      console.log('\n🚀 Executing Agent functions...\n');
      
      // 5. 함수 순차 실행
      const results = [];
      
      for (const item of keywords) {
        console.log(`▶️  Executing: ${item.keyword}`);
        
        try {
          const result = item.function(this.context);
          results.push({
            function: item.keyword,
            result: result,
            status: 'success'
          });
        } catch (error) {
          console.error(`❌ ${item.keyword} failed:`, error.message);
          results.push({
            function: item.keyword,
            error: error.message,
            status: 'failed'
          });
        }
        
        console.log('');
      }
      
      // 6. 결과 요약
      console.log('='  * 60);
      console.log('✅ Agent execution complete!\n');
      console.log('📊 Summary:');
      console.log(`  - Total functions: ${results.length}`);
      console.log(`  - Success: ${results.filter(r => r.status === 'success').length}`);
      console.log(`  - Failed: ${results.filter(r => r.status === 'failed').length}`);
      console.log('=' * 60);
      
      return {
        agentType: agentType,
        results: results,
        context: this.context
      };
      
    } catch (error) {
      console.error('❌ Agent execution failed:', error);
      throw error;
    }
  }
}


// ==================== CLI ====================

if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log(`
🌾 Mulberry Agent Image Lab - Model 3 Executor

Usage:
  node executor.js <image-path>

Example:
  node executor.js agent_crawler.mbconfig
  node executor.js agent_config.mbconfig

Supported formats:
  .mbconfig (Prompt Keywords Agent)
  .png (with agent metadata)
    `);
    process.exit(0);
  }
  
  const imagePath = args[0];
  
  if (!fs.existsSync(imagePath)) {
    console.error(`❌ File not found: ${imagePath}`);
    process.exit(1);
  }
  
  const executor = new AgentExecutor();
  
  executor.executeFromImage(imagePath)
    .then(result => {
      console.log('\n📄 Full Results:');
      console.log(JSON.stringify(result, null, 2));
    })
    .catch(error => {
      console.error('\n❌ Execution failed:', error);
      process.exit(1);
    });
}


// ==================== Export ====================

module.exports = {
  AgentPromptParser,
  AgentExecutor,
  AGENT_FUNCTIONS
};
