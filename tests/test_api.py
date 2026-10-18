"""API flow: upload -> status -> result. Models are faked, so no GPU needed."""
import io

import pytest

import src.pipeline as pipeline
from config import Settings
from src.app import create_app


@pytest.fixture()
def app(tmp_path, monkeypatch):
    settings = Settings(
        upload_dir=str(tmp_path / "uploads"),
        job_dir=str(tmp_path / "jobs"),
        llm_backend="mock",
        strategy="map_reduce",
    )

    def fake_extract(video_path, out_path):
        with open(out_path, "wb") as f:
            f.write(b"fake-audio")
        return out_path

    def fake_transcribe(audio_path, **kwargs):
        return [
            {"start": 0.0, "end": 5.0, "text": "welcome to the demo video"},
            {"start": 5.0, "end": 10.0, "text": "today we learn about summarization"},
        ]

    monkeypatch.setattr(pipeline, "extract_audio", fake_extract)
    monkeypatch.setattr(pipeline, "transcribe_audio", fake_transcribe)
    return create_app(settings=settings, sync_jobs=True)


@pytest.fixture()
def client(app):
    return app.test_client()


def _upload(client, filename="clip.mp4", strategy="map_reduce"):
    data = {
        "file": (io.BytesIO(b"fake-video-bytes"), filename),
        "strategy": strategy,
    }
    return client.post("/api/jobs", data=data, content_type="multipart/form-data")


def test_full_flow_upload_status_result(client):
    resp = _upload(client)
    assert resp.status_code == 202
    job_id = resp.get_json()["job_id"]

    status = client.get(f"/api/jobs/{job_id}").get_json()
    assert status["status"] == "done"
    assert status["progress"] == 100

    result = client.get(f"/api/jobs/{job_id}/result").get_json()
    assert "welcome to the demo video" in result["transcript"]
    assert result["summary"]  # mock client output
    assert result["strategy"] == "map_reduce"
    assert len(result["segments"]) == 2


def test_strategy_override_per_job(client):
    resp = _upload(client, strategy="stuff")
    job_id = resp.get_json()["job_id"]
    result = client.get(f"/api/jobs/{job_id}/result").get_json()
    assert result["strategy"] == "stuff"


def test_rejects_bad_extension(client):
    resp = _upload(client, filename="clip.exe")
    assert resp.status_code == 400


def test_rejects_missing_file(client):
    resp = client.post("/api/jobs", data={}, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_rejects_bad_strategy(client):
    resp = _upload(client, strategy="nope")
    assert resp.status_code == 400


def test_unknown_job_404(client):
    assert client.get("/api/jobs/deadbeef1234").status_code == 404
    assert client.get("/api/jobs/deadbeef1234/result").status_code == 404


def test_result_before_done_is_409(app, client):
    job_id = app.store.create("clip.mp4", "map_reduce")  # still queued
    resp = client.get(f"/api/jobs/{job_id}/result")
    assert resp.status_code == 409


def test_healthz(client):
    assert client.get("/healthz").get_json() == {"ok": True}
