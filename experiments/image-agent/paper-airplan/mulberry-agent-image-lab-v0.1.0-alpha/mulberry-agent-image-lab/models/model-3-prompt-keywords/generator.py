"""
Mulberry Agent Image Lab - Model 3: Prompt Keywords
Agent Image Generator with DALL-E 3

블로그 글 분석 → Agent 설정 → 프롬프트 키워드 삽입 → DALL-E 이미지 생성

@author CTO Koda
@date 2026-04-19
@version 1.0
"""

import openai
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import json
import requests
import os
from datetime import datetime


class PromptKeywordAgentGenerator:
    """프롬프트 키워드 방식으로 Agent 이미지 생성"""
    
    def __init__(self, openai_api_key=None):
        """
        초기화
        
        Args:
            openai_api_key: OpenAI API 키 (환경변수에서 자동 로드 가능)
        """
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Agent 타입별 키워드 매핑
        self.agent_keywords = {
            'CRAWLER': ['THINKEIN', 'ROUTIICG', 'PROZESSING'],
            'CONFIG': ['GITHUB_AUTOSETUP', 'RAILWAY_DEPLOY', 'WORKBENCH_SETUP'],
            'ANALYZER': ['THINKEIN', 'PROZESSING', 'ASTROFEN'],
            'MONITOR': ['ASTROFEN', 'PROCEGANG', 'MAIHESSHONE']
        }
    
    def build_agent_prompt(self, visual_description, agent_config):
        """
        시각적 설명 + Agent 키워드로 프롬프트 구성
        
        Args:
            visual_description: 시각적 설명 (예: "A beautiful Korean garden")
            agent_config: Agent 설정 dict
        
        Returns:
            완성된 프롬프트 문자열
        """
        agent_type = agent_config.get('type', 'CRAWLER')
        keywords = self.agent_keywords.get(agent_type, ['THINKEIN', 'PROZESSING'])
        
        # 키워드를 자연스럽게 삽입
        keyword_phrases = []
        
        if 'THINKEIN' in keywords:
            keyword_phrases.append("THINKEIN meditation elements")
        
        if 'ROUTIICG' in keywords:
            keyword_phrases.append("ROUTIICG pathways")
        
        if 'PROZESSING' in keywords:
            keyword_phrases.append("PROZESSING DATA flow")
        
        if 'GITHUB_AUTOSETUP' in keywords:
            keyword_phrases.append("GITHUB AUTOSETUP symbols")
        
        if 'RAILWAY_DEPLOY' in keywords:
            keyword_phrases.append("RAILWAY DEPLOY tracks")
        
        if 'ASTROFEN' in keywords:
            keyword_phrases.append("ASTROFEN celestial network")
        
        if 'PROCEGANG' in keywords:
            keyword_phrases.append("PROCEGANG parallel workers")
        
        # 프롬프트 조합
        full_prompt = f"{visual_description}, featuring {', and '.join(keyword_phrases)}"
        
        return full_prompt
    
    def generate_agent_image(self, visual_description, agent_config, output_path='agent.mbconfig'):
        """
        Agent 이미지 생성
        
        Args:
            visual_description: 시각적 설명
            agent_config: Agent 설정
            output_path: 출력 파일 경로
        
        Returns:
            생성된 이미지 파일 경로
        """
        print(f"🚀 Generating Agent Image...")
        print(f"Agent Type: {agent_config.get('type')}")
        
        # 1. 프롬프트 구성
        prompt = self.build_agent_prompt(visual_description, agent_config)
        
        print(f"\n📝 Prompt:")
        print(f"{prompt}\n")
        
        # 2. DALL-E 3로 이미지 생성
        print("🎨 Generating with DALL-E 3...")
        
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            print(f"✅ Image generated: {image_url}")
            
        except Exception as e:
            print(f"❌ DALL-E generation failed: {e}")
            raise
        
        # 3. 이미지 다운로드
        print("\n📥 Downloading image...")
        
        try:
            img_data = requests.get(image_url).content
            temp_path = 'temp_agent_image.png'
            
            with open(temp_path, 'wb') as f:
                f.write(img_data)
            
            print(f"✅ Downloaded to {temp_path}")
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            raise
        
        # 4. 메타데이터에 Agent 설정 저장
        print("\n💾 Adding metadata...")
        
        img = Image.open(temp_path)
        metadata = PngInfo()
        
        # 프롬프트 저장
        metadata.add_text("prompt", prompt)
        
        # Agent 설정 저장
        metadata.add_text("agent_type", agent_config.get('type', 'UNKNOWN'))
        metadata.add_text("agent_config", json.dumps(agent_config, ensure_ascii=False))
        
        # 버전 정보
        metadata.add_text("mulberry_version", "1.0")
        metadata.add_text("model", "prompt-keywords")
        metadata.add_text("generated_at", datetime.now().isoformat())
        
        # 저장
        img.save(output_path, pnginfo=metadata)
        
        print(f"✅ Saved to {output_path}")
        
        # 임시 파일 삭제
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        print(f"\n🎉 Agent Image generation complete!")
        print(f"📁 File: {output_path}")
        print(f"📊 Agent Type: {agent_config.get('type')}")
        
        return output_path
    
    def batch_generate(self, configs, output_dir='output'):
        """
        여러 Agent 이미지 일괄 생성
        
        Args:
            configs: Agent 설정 리스트
            output_dir: 출력 디렉토리
        
        Returns:
            생성된 파일 경로 리스트
        """
        os.makedirs(output_dir, exist_ok=True)
        generated_files = []
        
        for i, config in enumerate(configs, 1):
            print(f"\n{'='*60}")
            print(f"Generating {i}/{len(configs)}")
            print(f"{'='*60}\n")
            
            visual_desc = config.get('visual_description', 'A beautiful landscape')
            agent_config = config.get('agent_config', {})
            
            output_path = os.path.join(
                output_dir,
                f"agent_{agent_config.get('type', 'unknown').lower()}_{i}.mbconfig"
            )
            
            try:
                file_path = self.generate_agent_image(
                    visual_desc,
                    agent_config,
                    output_path
                )
                generated_files.append(file_path)
                
            except Exception as e:
                print(f"❌ Failed to generate {i}: {e}")
        
        print(f"\n{'='*60}")
        print(f"✅ Batch generation complete!")
        print(f"📊 Success: {len(generated_files)}/{len(configs)}")
        print(f"{'='*60}\n")
        
        return generated_files


# ==================== 사용 예시 ====================

if __name__ == '__main__':
    # Generator 초기화
    generator = PromptKeywordAgentGenerator(
        openai_api_key="sk-your-api-key"  # 실제 키로 교체
    )
    
    # 예시 1: Crawler Agent
    crawler_config = {
        "type": "CRAWLER",
        "action": "crawl",
        "target": "https://blog.naver.com",
        "endpoint": "https://api.mulberry.com/crawler/report",
        "interval": 300
    }
    
    generator.generate_agent_image(
        visual_description="A beautiful Korean traditional garden with cherry blossoms",
        agent_config=crawler_config,
        output_path="agent_crawler.mbconfig"
    )
    
    # 예시 2: Config Agent
    config_agent = {
        "type": "CONFIG",
        "action": "setup",
        "services": ["github", "railway", "huggingface"],
        "auto_deploy": True
    }
    
    generator.generate_agent_image(
        visual_description="A modern tech workspace with coding symbols",
        agent_config=config_agent,
        output_path="agent_config.mbconfig"
    )
    
    # 예시 3: 일괄 생성
    batch_configs = [
        {
            "visual_description": "Korean nature landscape",
            "agent_config": {
                "type": "CRAWLER",
                "target": "blog.naver.com"
            }
        },
        {
            "visual_description": "Tech startup office",
            "agent_config": {
                "type": "CONFIG",
                "services": ["github", "railway"]
            }
        }
    ]
    
    generator.batch_generate(batch_configs)
