# Contributing

Thanks for helping. This is a small, personal project, so keep changes small and easy to review.

## Before you send a change

- Run the tests: `python -m pytest tests/ -q`
- Keep the mock path working: with `LLM_BACKEND=mock` in `.env`, the app must run end to end with no model download and no API key.
- Do not commit a real API key, a real video with people in it, or a `.env` file. Use `.env.example` for settings.

## Reporting a problem

Open an issue and include:

- What you were doing (upload, transcribe, summarise)
- What happened, and what you expected instead
- Your Python version, and whether you used the CPU path or a GPU path

Do not include API keys, private videos, or personal details.
