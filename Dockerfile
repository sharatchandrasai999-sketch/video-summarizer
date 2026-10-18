# GPU-ready image: CUDA base + ffmpeg + the app.
# Build:  docker build -t video-summarizer .
# Run:    docker run --gpus all -p 5000:5000 --env-file .env video-summarizer
FROM nvidia/cuda:12.6.0-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv ffmpeg curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

COPY config.py .env.example ./
COPY src/ ./src/

EXPOSE 5000
# gunicorn: 2 workers are enough; the heavy work runs in background threads
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "600", "src.app:create_app()"]
