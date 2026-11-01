# Changelog

## 2026-11-01

- Added a CI workflow: Ubuntu, Python 3.11, ffmpeg, `pytest tests/ -q`. Its first runs completed successfully.
- Added a CPU-only Dockerfile (`Dockerfile.cpu`, Python slim + ffmpeg, mock backend by default). The original GPU Dockerfile is unchanged. Note: `Dockerfile.cpu` has not yet been built in Docker — build it once before claiming it as tested.
- Added CONTRIBUTING.md and a bug-report template.
- Added MIT LICENSE.

## Earlier

- Flask API: upload a video, get a summary and key points. Whisper transcription, chunking, three prompt strategies (stuff, map_reduce, refine), three LLM backends (mock, free Groq, self-hosted vLLM).
- 24 tests passing (verified locally, mock backend, no GPU).
- GPU Dockerfile and AWS deploy scripts. The app was not launched on AWS; it runs locally or in Docker.
- No versioned releases were tagged, so earlier changes are not listed by date here.
