# ShopMate 배포 가이드 (Deployment Guide)

본 문서는 ShopMate 를 Railway, Hugging Face, 그리고 Raspberry Pi 5(Edge) 에 배포하는 절차를 안내합니다.

---

## 1. 사전 준비 사항

### 1.1 필요 계정 및 도구
- **GitHub**: 소스 코드 저장소 (`mulberry-archive/ShopMate`)
- **Railway**: 백엔드 API 호스팅 (무료 티어 가능)
- **Hugging Face**: 모델 가중치 및 Spaces 호스팅
- **Raspberry Pi 5**: 8GB RAM 권장, 활성 쿨러 필수, Raspberry Pi OS (64-bit)
- **Chrome Browser**: GitHub 웹 인터페이스 및 MCP 기능 활용

### 1.2 환경 변수 설정
프로젝트 루트에 `.env` 파일을 생성하고 다음 변수를 설정합니다. (실제 값은 연구소 내부 공유 참조)

```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname
QDRANT_URL=http://qdrant-host:6333
REDIS_URL=redis://redis-host:6379

# AI Models
DEEPSEEK_API_KEY=your_deepseek_api_key
HUGGINGFACE_TOKEN=your_hf_token

# External APIs
OPENMARKET_API_KEY=your_api_key
PAYMENT_GATEWAY_KEY=your_pg_key

# Security
SECRET_KEY=your_secret_key_for_session
```

---

## 2. Cloud 백엔드 배포 (Railway)

### 2.1 Railway 프로젝트 생성
1. [Railway](https://railway.app/) 에 로그인합니다.
2. "New Project" 를 클릭하고 `ShopMate-Backend` 로 이름을 지정합니다.
3. "Deploy from GitHub repo" 를 선택하여 `mulberry-archive/ShopMate` 저장소를 연결합니다.

### 2.2 서비스 설정
- **Service**: `src/backend` 디렉토리를 루트로 설정.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: 위에서 작성한 `.env` 의 내용들을 Railway 대시보드에 입력합니다.

### 2.3 데이터베이스 연동
- Railway 에서 "PostgreSQL" 플러그인을 추가합니다.
- 자동으로 생성된 `DATABASE_URL` 을 환경 변수에 연결합니다.
- Qdrant 와 Redis 도 마찬가지로 플러그인 또는 외부 서비스를 연동합니다.

### 2.4 배포 확인
- Railway 가 제공하는 도메인 (예: `shopmate-backend.railway.app`) 으로 접속하여 API 헬스 체크 (`/health`) 가 성공하는지 확인합니다.

---

## 3. Hugging Face 모델 호스팅

### 3.1 모델 업로드
1. Hugging Face 에 로그인하고 새로운 레포지토리 (`mulberry-lab/shopmate-models`) 를 생성합니다.
2. 양자화된 DeepSeek 모델 (`DeepSeek-R1-Distill-Qwen-1.5B-GGUF`) 을 업로드합니다.
   ```bash
   # 예시 명령어 (로컬에서 gh CLI 사용 시)
   git lfs install
   git clone https://huggingface.co/mulberry-lab/shopmate-models
   cp path/to/model.gguf shopmate-models/
   cd shopmate-models && git add . && git commit -m "Add quantized model" && git push
   ```
   *CLI 가 없다면 웹 인터페이스에서 파일 업로드 기능을 사용합니다.*

### 3.2 Inference API 활용 (선택)
- 무거운 추론 작업은 Hugging Face Inference API 를 통해 수행하도록 설정할 수 있습니다.
- `AGENT_PROMPTS.md` 의 Cloud AI 설정을 참조하세요.

---

## 4. Edge Device 배포 (Raspberry Pi 5)

### 4.1 라즈베리 파이 초기 설정
1. **OS 설치**: Raspberry Pi Imager 를 사용하여 최신 Raspberry Pi OS (64-bit) 를 SD 카드에 설치합니다.
2. **기본 설정**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo raspi-config  # SSH, Wi-Fi, Locale 설정
   ```
3. **쿨러 확인**: 고성능 추론을 위해 활성 쿨러가 제대로 작동하는지 확인합니다.

### 4.2 자동 설치 스크립트 실행
프로젝트의 `scripts/setup_rpi.sh` 스크립트를 라즈베리 파이로 전송하여 실행합니다.

```bash
# scripts/setup_rpi.sh 내용 예시 (실제 파일로 생성됨)
#!/bin/bash
echo "🚀 Starting ShopMate Edge Setup..."

# 1. Python 환경 설정
sudo apt install -y python3-pip python3-venv libatlas-base-dev
python3 -m venv shopmate_env
source shopmate_env/bin/activate

# 2. 의존성 설치
pip install llama-cpp-python torch numpy

# 3. 모델 다운로드 (Hugging Face 에서)
echo "⬇️ Downloading DeepSeek 1.5B (4-bit)..."
# Hugging Face CLI 또는 wget 을 사용하여 모델 다운로드
# 예: huggingface-cli download mulberry-lab/shopmate-models model.gguf --local-dir ./models

# 4. 서비스 등록 (Systemd)
echo "📝 Registering systemd service..."
sudo bash -c 'cat > /etc/systemd/system/shopmate-edge.service << EOF
[Unit]
Description=ShopMate Edge Agent
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/ShopMate/src/edge
ExecStart=/home/pi/ShopMate/shopmate_env/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF'

sudo systemctl daemon-reload
sudo systemctl enable shopmate-edge
sudo systemctl start shopmate-edge

echo "✅ Setup Complete! Check status with: systemctl status shopmate-edge"
```

**실행 방법**:
1. 위 스크립트 내용을 라즈베리 파이의 `setup_rpi.sh` 로 저장합니다.
2. `chmod +x setup_rpi.sh` 권한을 부여합니다.
3. `./setup_rpi.sh` 를 실행합니다.

### 4.3 동작 확인
- `systemctl status shopmate-edge` 명령으로 서비스가 실행 중인지 확인합니다.
- 로그 확인: `journalctl -u shopmate-edge -f`

---

## 5. 프론트엔드 배포 (PWA)

### 5.1 빌드
```bash
cd src/frontend
npm install
npm run build
```

### 5.2 정적 파일 호스팅
- Railway 에서 별도의 "Static Site" 서비스를 추가하거나, Vercel/Netlify 를 활용합니다.
- 빌드된 `dist/` 폴더 내용을 업로드합니다.
- 환경 변수 `VITE_API_URL` 을 Railway 백엔드 URL 로 설정합니다.

---

## 6. 유지보수 및 모니터링

- **로그 수집**: Railway 대시보드와 라즈베리 파이의 `journalctl` 을 통해 실시간 로그를 모니터링합니다.
- **자동 업데이트**: GitHub Actions 를 활용하여 코드 푸시 시 자동으로 Railway 와 라즈베리 파이에 배포되도록 설정합니다.
- **백업**: PostgreSQL DB 는 매일 새벽에 자동으로 백업되도록 크론 잡을 설정합니다.

---

*배포 관련 문의는 Mulberry Research Lab 이슈 트래커를 이용해 주세요.*
*작성자: Jr. RyuWon*
