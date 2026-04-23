"""
Mulberry Agent Image Lab - Content Analyzer
블로그 글 분석 → Agent 설정 자동 생성

@author CTO Koda
@date 2026-04-19
@version 1.0
"""

import openai
import json
import os
import re
from typing import Dict, List, Optional


class ContentAnalyzer:
    """블로그 글 분석기"""
    
    def __init__(self, openai_api_key=None):
        """초기화"""
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def analyze(self, blog_content: str) -> Dict:
        """
        블로그 글 분석
        
        Args:
            blog_content: 블로그 글 내용
        
        Returns:
            분석 결과 dict
        """
        print("🔍 Analyzing blog content...")
        print(f"📝 Content length: {len(blog_content)} characters\n")
        
        try:
            # GPT-4로 분석
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 블로그 글을 분석해서 적절한 AI Agent 설정을 추출하는 전문가입니다.
                        
                        블로그 글을 분석하고 다음 정보를 JSON 형식으로 반환하세요:
                        
                        {
                            "topic": "주제 (한글)",
                            "topic_en": "주제 (영문)",
                            "keywords": ["키워드1", "키워드2", "키워드3"],
                            "agent_type": "CRAWLER | ANALYZER | CONFIG | MONITOR",
                            "target": "타겟 URL (있다면)",
                            "actions": ["액션1", "액션2"],
                            "visual_theme": "이미지 시각 테마 (영문)",
                            "prompt_keywords": ["THINKEIN", "ROUTIICG", ...],
                            "confidence": 0.0 ~ 1.0
                        }
                        
                        Agent 타입 결정 기준:
                        - CRAWLER: 크롤링, 데이터 수집, 웹 스크래핑 관련
                        - ANALYZER: 데이터 분석, AI 분석, 통계 관련
                        - CONFIG: 환경 설정, 개발 환경, 배포 관련
                        - MONITOR: 모니터링, 추적, 알림 관련
                        
                        Prompt Keywords:
                        - THINKEIN: AI 엔진, 사고
                        - ROUTIICG: 라우팅, 네트워크
                        - PROZESSING: 데이터 처리
                        - ASTROFEN: 서버 연결
                        - GITHUB_AUTOSETUP: GitHub 설정
                        - RAILWAY_DEPLOY: Railway 배포
                        - WORKBENCH_SETUP: 워크벤치 설정
                        - PROCEGANG: 병렬 처리
                        - MAIHESSHONE: 유지보수
                        """
                    },
                    {
                        "role": "user",
                        "content": f"이 블로그 글을 분석해주세요:\n\n{blog_content}"
                    }
                ],
                temperature=0.3
            )
            
            # JSON 파싱
            result_text = response.choices[0].message.content
            
            # JSON 추출 (```json ... ``` 제거)
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            
            analysis = json.loads(result_text)
            
            print("✅ Analysis complete!\n")
            print(f"📊 Topic: {analysis.get('topic')}")
            print(f"🎯 Agent Type: {analysis.get('agent_type')}")
            print(f"🔑 Keywords: {', '.join(analysis.get('keywords', []))}")
            print(f"📈 Confidence: {analysis.get('confidence', 0):.1%}\n")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            raise
    
    def generate_agent_config(self, analysis: Dict) -> Dict:
        """
        분석 결과 → Agent 설정 생성
        
        Args:
            analysis: 분석 결과
        
        Returns:
            Agent 설정 dict
        """
        agent_type = analysis.get('agent_type', 'CRAWLER')
        
        config = {
            'type': agent_type,
            'topic': analysis.get('topic'),
            'version': '1.0'
        }
        
        # Agent 타입별 설정
        if agent_type == 'CRAWLER':
            config.update({
                'action': 'crawl',
                'target': analysis.get('target', ''),
                'keywords': analysis.get('keywords', []),
                'endpoint': 'https://api.mulberry.com/crawler/report',
                'interval': 300
            })
        
        elif agent_type == 'ANALYZER':
            config.update({
                'action': 'analyze',
                'methods': analysis.get('actions', []),
                'data_types': analysis.get('keywords', []),
                'endpoint': 'https://api.mulberry.com/analyzer/report'
            })
        
        elif agent_type == 'CONFIG':
            config.update({
                'action': 'setup',
                'services': analysis.get('actions', []),
                'auto_deploy': True,
                'targets': ['github', 'railway', 'huggingface']
            })
        
        elif agent_type == 'MONITOR':
            config.update({
                'action': 'monitor',
                'targets': analysis.get('actions', []),
                'interval': 300,
                'alerts': True
            })
        
        return config
    
    def analyze_and_generate(self, blog_content: str) -> tuple:
        """
        블로그 글 분석 + Agent 설정 생성 (통합)
        
        Args:
            blog_content: 블로그 글
        
        Returns:
            (분석 결과, Agent 설정, 시각적 설명)
        """
        # 분석
        analysis = self.analyze(blog_content)
        
        # Agent 설정 생성
        agent_config = self.generate_agent_config(analysis)
        
        # 시각적 설명
        visual_description = self._build_visual_description(analysis)
        
        return analysis, agent_config, visual_description
    
    def _build_visual_description(self, analysis: Dict) -> str:
        """
        분석 결과 → 시각적 설명 생성
        
        Args:
            analysis: 분석 결과
        
        Returns:
            시각적 설명 문자열
        """
        theme = analysis.get('visual_theme', 'modern technology')
        topic_en = analysis.get('topic_en', 'technology')
        
        # 기본 템플릿
        descriptions = [
            f"A beautiful Korean-style infographic about {topic_en}",
            f"featuring {theme}",
            "with clean layout and modern design elements",
            "professional look suitable for blog post"
        ]
        
        return ", ".join(descriptions)


# ==================== 사용 예시 ====================

if __name__ == '__main__':
    analyzer = ContentAnalyzer(
        openai_api_key="sk-your-api-key"  # 실제 키로 교체
    )
    
    # 예시 블로그 글
    blog_post = """
# Mulberry로 네이버 블로그 크롤링하기

안녕하세요! 오늘은 Mulberry Agent를 사용해서
네이버 블로그를 자동으로 크롤링하는 방법을 알려드릴게요.

## 크롤링이란?

웹 크롤링은 웹사이트에서 자동으로 데이터를 수집하는 기술입니다.
네이버 블로그에서 포스트 제목, 내용, 날짜 등을 추출할 수 있어요.

## 시작하기

1. Mulberry Agent 설치
2. blog.naver.com 타겟 설정
3. 크롤링 시작!

정말 간단하죠? 한번 시작해볼까요!
    """
    
    # 분석 + 설정 생성
    analysis, agent_config, visual_desc = analyzer.analyze_and_generate(blog_post)
    
    print("="*60)
    print("📊 Final Results:\n")
    print("Analysis:", json.dumps(analysis, indent=2, ensure_ascii=False))
    print("\nAgent Config:", json.dumps(agent_config, indent=2, ensure_ascii=False))
    print("\nVisual Description:", visual_desc)
    print("="*60)
