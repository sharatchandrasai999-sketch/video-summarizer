"""The full pipeline: video -> audio -> transcript -> chunks -> summary.

Steps update the job record so the API can report progress. The transcribe
and summarize steps accept injected functions so tests can run without
models or a GPU.
"""
import os

from src.audio import extract_audio
from src.chunking import chunk_segments
from src.summarize import make_client, summarize
from src.transcribe import transcribe_audio


def run_job(job_id: str, video_path: str, store, settings,
            transcribe_fn=None, summarize_fn=None):
    try:
        store.update(job_id, status="extracting", progress=5)
        audio_path = os.path.join(settings.job_dir, job_id, "audio.wav")
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        extract_audio(video_path, audio_path)

        store.update(job_id, status="transcribing", progress=25)
        transcribe = transcribe_fn or transcribe_audio
        segments = transcribe(
            audio_path,
            model_name=settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute,
        )
        if not segments:
            raise RuntimeError("No speech found in the audio.")

        store.update(job_id, status="summarizing", progress=60)
        chunks = chunk_segments(
            segments,
            max_words=settings.max_chunk_words,
            overlap_words=settings.chunk_overlap_words,
        )
        if summarize_fn is not None:
            result = summarize_fn(chunks)
        else:
            result = summarize(chunks, settings.strategy, make_client(settings))

        result["transcript"] = " ".join(s["text"] for s in segments)
        result["segments"] = segments
        result["strategy"] = settings.strategy
        store.update(job_id, status="done", progress=100, result=result)
    except Exception as exc:  # noqa: BLE001 - surfaced to the API as job error
        store.update(job_id, status="failed", error=str(exc))
