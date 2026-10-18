"""Talk to the LLM (Mixtral) and run the chosen prompt strategy.

Backends:
- MockClient        no model, placeholder output (tests / dry runs)
- OpenAICompatClient any OpenAI-style chat API (a vLLM server on your GPU box)
- GroqClient         free hosted Mixtral through the Groq API
"""
import json
import re

import requests

from src import prompts


class LLMClient:
    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class MockClient(LLMClient):
    def complete(self, system: str, user: str) -> str:
        snippet = user.replace("\n", " ")[:160]
        return f"[mock summary] {snippet} ..."


class OpenAICompatClient(LLMClient):
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 300):
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, system: str, user: str) -> str:
        resp = requests.post(
            self.url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.3,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


class GroqClient(OpenAICompatClient):
    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b"):
        super().__init__("https://api.groq.com/openai/v1", api_key, model)


def make_client(settings) -> LLMClient:
    backend = settings.llm_backend
    if backend == "groq":
        if not settings.groq_api_key:
            raise RuntimeError("LLM_BACKEND=groq needs GROQ_API_KEY set")
        return GroqClient(settings.groq_api_key, settings.llm_model)
    if backend == "vllm":
        return OpenAICompatClient(settings.vllm_url, settings.vllm_api_key, settings.llm_model)
    if backend == "mock":
        return MockClient()
    raise RuntimeError(f"Unknown LLM_BACKEND: {backend}")


def summarize(chunks, strategy: str, client: LLMClient) -> dict:
    if strategy not in prompts.STRATEGIES:
        raise ValueError(f"Unknown strategy {strategy!r}, pick one of {prompts.STRATEGIES}")
    if strategy == "stuff":
        return _run_stuff(chunks, client)
    if strategy == "map_reduce":
        return _run_map_reduce(chunks, client)
    return _run_refine(chunks, client)


def _run_stuff(chunks, client):
    transcript = "\n".join(c["text"] for c in chunks)
    raw = client.complete(prompts.SYSTEM, prompts.stuff_prompt(transcript))
    return _parse_loose(raw)


def _run_map_reduce(chunks, client):
    mapped = []
    for i, chunk in enumerate(chunks, 1):
        out = client.complete(
            prompts.SYSTEM, prompts.map_prompt(chunk["text"], chunk["start"], chunk["end"])
        )
        mapped.append(f"--- Part {i} ---\n{out}")
    raw = client.complete(prompts.SYSTEM, prompts.reduce_prompt("\n".join(mapped)))
    result = _parse_json(raw)
    chapters = result.get("chapters") or [
        {"title": f"Part {i + 1}", "start": c["start"]} for i, c in enumerate(chunks)
    ]
    return {
        "summary": result.get("summary", raw),
        "key_points": result.get("key_points", []),
        "chapters": chapters,
    }


def _run_refine(chunks, client):
    summary = client.complete(prompts.SYSTEM, prompts.map_prompt(
        chunks[0]["text"], chunks[0]["start"], chunks[0]["end"]))
    for chunk in chunks[1:]:
        summary = client.complete(
            prompts.SYSTEM, prompts.refine_prompt(summary, chunk["text"]))
    return _parse_loose(summary)


def _parse_loose(raw: str) -> dict:
    """Split 'summary, then dash bullets' text into a result dict."""
    lines = [ln.strip() for ln in raw.splitlines()]
    summary_lines, points = [], []
    for ln in lines:
        if re.match(r"^[-*\u2022]\s+", ln):
            points.append(re.sub(r"^[-*\u2022]\s+", "", ln))
        elif ln:
            summary_lines.append(ln)
    return {
        "summary": " ".join(summary_lines),
        "key_points": points,
        "chapters": [],
    }


def _parse_json(raw: str) -> dict:
    """Pull a JSON object out of model output, even with extra text around it."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
