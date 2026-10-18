#!/bin/bash
# Runs once when the EC2 box first boots.
# Use with the AWS Deep Learning AMI (it already has NVIDIA drivers).
set -e

apt-get update -qq
apt-get install -y -qq docker.io git
systemctl start docker
systemctl enable docker

# --- the app (Whisper on GPU) ---
git clone https://github.com/YOUR_USER/video-summarizer.git /opt/video-summarizer
cd /opt/video-summarizer
cat > .env <<'EOF'
WHISPER_MODEL=small
WHISPER_DEVICE=cuda
WHISPER_COMPUTE=float16
LLM_BACKEND=vllm
LLM_MODEL=casperhansen/mixtral-8x7b-instruct-v0.1-awq
VLLM_URL=http://localhost:8000/v1
SUMMARY_STRATEGY=map_reduce
EOF
docker build -t video-summarizer .

# --- Mixtral itself, served by vLLM on all 4 GPUs (needs g5.12xlarge) ---
docker run -d --gpus all --name vllm -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model casperhansen/mixtral-8x7b-instruct-v0.1-awq \
  --tensor-parallel-size 4 --max-model-len 16384

# --- the Flask API, talking to vLLM next door ---
docker run -d --gpus all --name api -p 5000:5000 --env-file .env video-summarizer

echo "API will be live at http://<box-ip>:5000 once vLLM finishes loading (~5 min)"
