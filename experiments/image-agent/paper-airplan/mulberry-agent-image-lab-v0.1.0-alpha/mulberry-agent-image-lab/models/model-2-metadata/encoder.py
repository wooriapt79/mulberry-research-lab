"""
Mulberry Agent Image Lab - Model 2: Metadata Encoding
PNG/EXIF 메타데이터에 Agent 저장

@author CTO Koda
@date 2026-04-19
@version 1.0
"""

from PIL import Image
from PIL.PngImagePlugin import PngInfo
import json
from typing import Dict
from datetime import datetime


class MetadataEncoder:
    """메타데이터 방식으로 Agent 인코딩"""
    
    def __init__(self):
        self.version = "1.0"
    
    def encode_agent(self, image_path: str, agent_config: Dict, output_path: str = 'agent.mbimg'):
        """
        PNG 메타데이터에 Agent 저장
        
        Args:
            image_path: 원본 이미지 경로
            agent_config: Agent 설정
            output_path: 출력 파일 경로
        
        Returns:
            출력 파일 경로
        """
        print(f"💾 Encoding Agent to metadata...")
        print(f"📁 Input: {image_path}")
        print(f"📁 Output: {output_path}\n")
        
        # 1. 이미지 로드
        img = Image.open(image_path)
        
        # 2. PNG 메타데이터 생성
        metadata = PngInfo()
        
        # Agent 정보
        metadata.add_text("mulberry_agent", "true")
        metadata.add_text("mulberry_version", self.version)
        metadata.add_text("agent_type", agent_config.get('type', 'UNKNOWN'))
        metadata.add_text("agent_config", json.dumps(agent_config, ensure_ascii=False))
        metadata.add_text("generated_at", datetime.now().isoformat())
        metadata.add_text("model", "metadata-encoding")
        
        # 추가 정보
        if 'topic' in agent_config:
            metadata.add_text("topic", agent_config['topic'])
        
        if 'target' in agent_config:
            metadata.add_text("target", agent_config['target'])
        
        # 3. 저장
        img.save(output_path, format='PNG', pnginfo=metadata)
        
        # 파일 크기 확인
        import os
        file_size = os.path.getsize(output_path)
        config_size = len(json.dumps(agent_config))
        
        print(f"📊 Agent config size: {config_size} bytes")
        print(f"📊 Output file size: {file_size} bytes")
        print(f"✅ Encoding complete!")
        print(f"📁 Saved: {output_path}\n")
        
        return output_path
    
    def decode_agent(self, image_path: str) -> Dict:
        """
        PNG 메타데이터에서 Agent 추출
        
        Args:
            image_path: Agent 이미지 경로
        
        Returns:
            Agent 설정 dict
        """
        print(f"📖 Decoding Agent from metadata...")
        print(f"📁 Input: {image_path}\n")
        
        # 1. 이미지 로드
        img = Image.open(image_path)
        
        # 2. 메타데이터 읽기
        metadata = img.info
        
        # 3. Agent 확인
        if not metadata.get('mulberry_agent'):
            raise ValueError("Not a Mulberry Agent image!")
        
        # 4. Agent 정보 추출
        agent_type = metadata.get('agent_type')
        agent_config_str = metadata.get('agent_config')
        version = metadata.get('mulberry_version')
        generated_at = metadata.get('generated_at')
        
        print(f"✅ Mulberry Agent detected!")
        print(f"📋 Version: {version}")
        print(f"📋 Agent Type: {agent_type}")
        print(f"📋 Generated: {generated_at}\n")
        
        # 5. JSON 파싱
        agent_config = json.loads(agent_config_str)
        
        return agent_config
    
    def list_metadata(self, image_path: str):
        """메타데이터 전체 조회"""
        img = Image.open(image_path)
        metadata = img.info
        
        print(f"📋 All Metadata for {image_path}:\n")
        for key, value in metadata.items():
            if key.startswith('mulberry') or key in ['agent_type', 'agent_config', 'topic', 'target']:
                print(f"  {key}: {value[:100] if len(str(value)) > 100 else value}")
        print()


# ==================== 사용 예시 ====================

if __name__ == '__main__':
    encoder = MetadataEncoder()
    
    # 예시 1: Config Agent
    config_agent = {
        "type": "CONFIG",
        "action": "setup",
        "services": ["github", "railway", "huggingface"],
        "auto_deploy": True,
        "topic": "Mulberry 환경 설정",
        "settings": {
            "github": {
                "repo_name": "my-mulberry-project",
                "private": False
            },
            "railway": {
                "service": "mulberry-mission-control",
                "region": "asia-northeast1"
            }
        }
    }
    
    # 인코딩
    encoder.encode_agent(
        image_path='sample_image.png',
        agent_config=config_agent,
        output_path='agent_config.mbimg'
    )
    
    # 메타데이터 조회
    encoder.list_metadata('agent_config.mbimg')
    
    # 디코딩
    decoded_config = encoder.decode_agent('agent_config.mbimg')
    
    print("="*60)
    print("📊 Decoded Agent Config:")
    print(json.dumps(decoded_config, indent=2, ensure_ascii=False))
    print("="*60)
