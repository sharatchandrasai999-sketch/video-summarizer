"""All settings come from environment variables, with sane defaults.

Copy .env.example to .env and change what you need. Nothing here is secret.
"""
import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()  # lets plain `python src/app.py` pick up the .env file
except ImportError:
    pass


@dataclass
class Settings:
    # folders
    upload_dir: str = os.environ.get("UPLOAD_DIR", "uploads")
    job_dir: str = os.environ.get("JOB_DIR", "jobs")

    # whisper (speech -> text)
    whisper_model: str = os.environ.get("WHISPER_MODEL", "small")
    whisper_device: str = os.environ.get("WHISPER_DEVICE", "cpu")  # "cuda" on a GPU box
    whisper_compute: str = os.environ.get("WHISPER_COMPUTE", "int8")

    # LLM (text -> summary). Backend choices:
    #   "mock" - no model, returns placeholder text (tests, dry runs)
    #   "groq" - free hosted Mixtral via Groq API (needs GROQ_API_KEY)
    #   "vllm" - your own Mixtral on a GPU box via a vLLM server
    llm_backend: str = os.environ.get("LLM_BACKEND", "mock")
    # Groq retired Mixtral and gates Llama 3.3 behind enterprise, so the free
    # default is OpenAI's gpt-oss-120b (verified live via Groq's /models).
    # For the vLLM backend, set LLM_MODEL to the model your server serves.
    llm_model: str = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")
    groq_api_key: str = os.environ.get("GROQ_API_KEY", "")
    vllm_url: str = os.environ.get("VLLM_URL", "http://localhost:8000/v1")
    vllm_api_key: str = os.environ.get("VLLM_API_KEY", "none")

    # summarization
    strategy: str = os.environ.get("SUMMARY_STRATEGY", "map_reduce")  # stuff | map_reduce | refine
    max_chunk_words: int = int(os.environ.get("MAX_CHUNK_WORDS", "1200"))
    chunk_overlap_words: int = int(os.environ.get("CHUNK_OVERLAP_WORDS", "100"))

    # uploads
    max_upload_mb: int = int(os.environ.get("MAX_UPLOAD_MB", "500"))
    allowed_exts: set = field(default_factory=lambda: {"mp4", "mp3", "wav", "mov", "mkv", "webm", "m4a"})


settings = Settings()
