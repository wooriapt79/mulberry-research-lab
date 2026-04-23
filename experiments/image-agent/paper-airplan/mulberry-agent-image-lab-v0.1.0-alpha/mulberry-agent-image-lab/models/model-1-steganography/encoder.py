"""
Mulberry Agent Image Lab - Model 1: Steganography
LSB (Least Significant Bit) 방식 Agent 인코더

이미지 픽셀의 마지막 비트에 Agent 데이터 숨김

@author CTO Koda
@date 2026-04-19
@version 1.0
"""

from PIL import Image
import numpy as np
import json
import zlib
import struct
from typing import Dict


class SteganographyEncoder:
    """스테가노그래피 방식으로 Agent 인코딩"""
    
    def __init__(self):
        self.signature = b'MLBY'  # Mulberry 시그니처
        self.version = 1
    
    def encode_agent(self, image_path: str, agent_config: Dict, output_path: str = 'agent.mba'):
        """
        이미지에 Agent 데이터 인코딩
        
        Args:
            image_path: 원본 이미지 경로
            agent_config: Agent 설정
            output_path: 출력 파일 경로
        
        Returns:
            출력 파일 경로
        """
        print(f"🔒 Encoding Agent to image...")
        print(f"📁 Input: {image_path}")
        print(f"📁 Output: {output_path}\n")
        
        # 1. 이미지 로드
        img = Image.open(image_path)
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = np.array(img)
        height, width, channels = pixels.shape
        
        print(f"📐 Image size: {width}x{height}")
        print(f"💾 Available capacity: ~{(width * height * 3) // 8} bytes\n")
        
        # 2. Agent 설정을 JSON으로 직렬화
        config_json = json.dumps(agent_config, ensure_ascii=False)
        config_bytes = config_json.encode('utf-8')
        
        # 3. 압축
        compressed = zlib.compress(config_bytes, level=9)
        
        print(f"📊 Original size: {len(config_bytes)} bytes")
        print(f"📊 Compressed size: {len(compressed)} bytes")
        print(f"📊 Compression ratio: {len(compressed)/len(config_bytes)*100:.1f}%\n")
        
        # 4. 헤더 생성
        # 시그니처(4) + 버전(1) + 길이(4) = 9 bytes
        header = self.signature + struct.pack('B', self.version) + struct.pack('I', len(compressed))
        
        # 5. 전체 데이터
        data_to_encode = header + compressed
        
        # 용량 체크
        max_capacity = (width * height * 3) // 8
        if len(data_to_encode) > max_capacity:
            raise ValueError(f"Data too large! {len(data_to_encode)} > {max_capacity}")
        
        # 6. Binary로 변환
        data_bits = ''.join(format(byte, '08b') for byte in data_to_encode)
        
        print(f"🔐 Encoding {len(data_bits)} bits...")
        
        # 7. LSB에 인코딩
        flat_pixels = pixels.flatten()
        
        for i, bit in enumerate(data_bits):
            # 마지막 비트 교체
            flat_pixels[i] = (flat_pixels[i] & 0xFE) | int(bit)
        
        # 8. 이미지 재구성
        encoded_pixels = flat_pixels.reshape(pixels.shape)
        encoded_img = Image.fromarray(encoded_pixels.astype('uint8'))
        
        # 9. 저장 (PNG로 저장 - 무손실)
        encoded_img.save(output_path, format='PNG')
        
        print(f"✅ Encoding complete!")
        print(f"📁 Saved: {output_path}\n")
        
        return output_path
    
    def decode_agent(self, image_path: str) -> Dict:
        """
        이미지에서 Agent 데이터 디코딩
        
        Args:
            image_path: Agent 이미지 경로
        
        Returns:
            Agent 설정 dict
        """
        print(f"🔓 Decoding Agent from image...")
        print(f"📁 Input: {image_path}\n")
        
        # 1. 이미지 로드
        img = Image.open(image_path)
        pixels = np.array(img)
        flat_pixels = pixels.flatten()
        
        # 2. LSB 추출
        print(f"🔍 Extracting LSB bits...")
        
        # 헤더 읽기 (9 bytes = 72 bits)
        header_bits = ''.join(str(pixel & 1) for pixel in flat_pixels[:72])
        header_bytes = bytearray()
        
        for i in range(0, 72, 8):
            byte = header_bits[i:i+8]
            header_bytes.append(int(byte, 2))
        
        # 3. 헤더 파싱
        signature = bytes(header_bytes[:4])
        version = header_bytes[4]
        data_length = struct.unpack('I', bytes(header_bytes[5:9]))[0]
        
        if signature != self.signature:
            raise ValueError(f"Invalid signature! Expected {self.signature}, got {signature}")
        
        print(f"✅ Valid Mulberry Agent detected!")
        print(f"📊 Version: {version}")
        print(f"📊 Data length: {data_length} bytes\n")
        
        # 4. 압축된 데이터 추출
        total_bits_needed = (9 + data_length) * 8
        data_bits = ''.join(str(pixel & 1) for pixel in flat_pixels[72:total_bits_needed])
        
        # Binary → Bytes
        compressed_data = bytearray()
        for i in range(0, len(data_bits), 8):
            byte = data_bits[i:i+8]
            if len(byte) == 8:
                compressed_data.append(int(byte, 2))
        
        # 5. 압축 해제
        print(f"📦 Decompressing data...")
        config_bytes = zlib.decompress(bytes(compressed_data))
        
        # 6. JSON 파싱
        config_json = config_bytes.decode('utf-8')
        agent_config = json.loads(config_json)
        
        print(f"✅ Decoding complete!")
        print(f"📋 Agent Type: {agent_config.get('type')}\n")
        
        return agent_config


# ==================== 사용 예시 ====================

if __name__ == '__main__':
    encoder = SteganographyEncoder()
    
    # 예시 1: Agent 인코딩
    agent_config = {
        "type": "CRAWLER",
        "action": "crawl",
        "target": "https://blog.naver.com",
        "endpoint": "https://api.mulberry.com/crawler/report",
        "interval": 300,
        "keywords": ["블로그", "크롤링", "데이터"],
        "settings": {
            "depth": 3,
            "timeout": 30,
            "retry": 3
        }
    }
    
    # 인코딩
    encoder.encode_agent(
        image_path='sample_image.png',
        agent_config=agent_config,
        output_path='agent_crawler.mba'
    )
    
    # 디코딩
    decoded_config = encoder.decode_agent('agent_crawler.mba')
    
    print("="*60)
    print("📊 Decoded Agent Config:")
    print(json.dumps(decoded_config, indent=2, ensure_ascii=False))
    print("="*60)
