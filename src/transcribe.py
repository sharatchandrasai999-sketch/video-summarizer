"""Speech -> text with Whisper (faster-whisper build).

The model loads once and is reused for every job. On a GPU box set
WHISPER_DEVICE=cuda and WHISPER_COMPUTE=float16 for a big speedup.
"""
import os

from faster_whisper import WhisperModel

_model = None
_model_key = None


def _sanitize_no_proxy():
    """huggingface_hub's vendored httpx crashes on bracketed IPv6 entries
    like [::1] in no_proxy (it builds a bad URL pattern from them).
    Strip the brackets; bare ::1 is handled fine."""
    for var in ("no_proxy", "NO_PROXY"):
        val = os.environ.get(var)
        if not val or "[" not in val:
            continue
        parts = []
        for piece in val.split(","):
            piece = piece.strip()
            if piece.startswith("[") and piece.endswith("]") and ":" in piece:
                piece = piece[1:-1]
            parts.append(piece)
        os.environ[var] = ",".join(parts)


_sanitize_no_proxy()


def get_model(model_name: str, device: str, compute_type: str) -> WhisperModel:
    global _model, _model_key
    key = (model_name, device, compute_type)
    if _model is None or _model_key != key:
        _model = WhisperModel(model_name, device=device, compute_type=compute_type)
        _model_key = key
    return _model


def transcribe_audio(audio_path: str, model_name: str = "small",
                     device: str = "cpu", compute_type: str = "int8"):
    """Return a list of {"start": seconds, "end": seconds, "text": str}."""
    model = get_model(model_name, device, compute_type)
    segments, _info = model.transcribe(audio_path, beam_size=5)
    out = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            out.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": text})
    return out
