"""The no_proxy sanitizer: bracketed IPv6 must not crash httpx."""
import importlib
import os

import src.transcribe as transcribe


def test_sanitize_no_proxy_strips_brackets(monkeypatch):
    monkeypatch.setenv("no_proxy", "localhost,[::1],192.168.0.1,[fd8b::1]")
    monkeypatch.setenv("NO_PROXY", "localhost,[::1]")
    importlib.reload(transcribe)
    assert transcribe.os.environ["no_proxy"] == "localhost,::1,192.168.0.1,fd8b::1"
    assert transcribe.os.environ["NO_PROXY"] == "localhost,::1"


def test_sanitize_no_proxy_leaves_clean_values(monkeypatch):
    monkeypatch.setenv("no_proxy", "localhost,127.0.0.1")
    monkeypatch.delenv("NO_PROXY", raising=False)
    importlib.reload(transcribe)
    assert transcribe.os.environ["no_proxy"] == "localhost,127.0.0.1"


def test_httpx_accepts_sanitized_proxies():
    # the real crash: URLPattern on no_proxy-derived entries
    from httpx2._utils import get_environment_proxies, URLPattern

    for key in get_environment_proxies():
        URLPattern(key)  # must not raise
