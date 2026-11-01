"""Flask API.

POST /api/jobs            upload a video file  -> {"job_id": ...}
GET  /api/jobs/<job_id>   job status + progress
GET  /api/jobs/<job_id>/result   the summary (when done)
GET  /healthz             health check
GET  /                    tiny upload page
"""
import os
import sys
import threading
from functools import partial

# make `python src/app.py` work from anywhere: project root on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings as default_settings
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

from src.jobs import JobStore
from src.pipeline import run_job

HOME_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>Video Summarizer</title>
<style>body{font-family:system-ui;max-width:640px;margin:40px auto;padding:0 16px}
input,select,button{font-size:16px;margin:6px 0}button{padding:8px 18px}</style>
</head><body>
<h2>Video Summarizer</h2>
<p>Upload a video. You get back a written summary and key points.</p>
<form action="/api/jobs" method="post" enctype="multipart/form-data">
<input type="file" name="file" accept="video/*,audio/*" required><br>
<label>Plan:
<select name="strategy">
<option value="map_reduce">Map-reduce (best for long videos)</option>
<option value="stuff">Stuff (fast, short videos)</option>
<option value="refine">Refine (one flowing story)</option>
</select></label><br>
<button type="submit">Summarize</button>
</form>
<p>Tip: check <code>/api/jobs/&lt;job_id&gt;</code> for progress,
<code>/api/jobs/&lt;job_id&gt;/result</code> for the summary.</p>
</body></html>"""


def create_app(settings=None, sync_jobs=False):
    settings = settings or default_settings
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = settings.max_upload_mb * 1024 * 1024
    os.makedirs(settings.upload_dir, exist_ok=True)
    store = JobStore(settings.job_dir)
    app.store = store
    app.settings = settings

    def start_job(job_id, video_path):
        if sync_jobs:
            run_job(job_id, video_path, store, settings)
        else:
            thread = threading.Thread(
                target=run_job, args=(job_id, video_path, store, settings), daemon=True
            )
            thread.start()

    # allow tests to inject fakes without touching the real pipeline
    app.start_job = start_job

    @app.get("/")
    def home():
        return HOME_PAGE

    @app.get("/healthz")
    def healthz():
        return jsonify({"ok": True})

    @app.post("/api/jobs")
    def create_job():
        if "file" not in request.files:
            return jsonify({"error": "send the video as form field 'file'"}), 400
        f = request.files["file"]
        if not f.filename:
            return jsonify({"error": "empty filename"}), 400
        ext = f.filename.rsplit(".", 1)[-1].lower()
        if ext not in settings.allowed_exts:
            return jsonify({"error": f".{ext} not allowed"}), 400
        strategy = request.form.get("strategy", settings.strategy)
        from . import prompts
        if strategy not in prompts.STRATEGIES:
            return jsonify({"error": f"strategy must be one of {prompts.STRATEGIES}"}), 400

        job_id = store.create(secure_filename(f.filename), strategy)
        video_path = os.path.join(settings.upload_dir, job_id + "." + ext)
        f.save(video_path)
        # per-job strategy override
        job_settings = _with_strategy(settings, strategy)
        runner = partial(run_job, job_id, video_path, store, job_settings)
        if sync_jobs:
            runner()
        else:
            threading.Thread(target=runner, daemon=True).start()
        return jsonify({"job_id": job_id, "status": "queued"}), 202

    @app.get("/api/jobs/<job_id>")
    def job_status(job_id):
        job = store.get(job_id)
        if job is None:
            return jsonify({"error": "job not found"}), 404
        job = dict(job)
        job.pop("result", None)  # status endpoint stays small
        return jsonify(job)

    @app.get("/api/jobs/<job_id>/result")
    def job_result(job_id):
        job = store.get(job_id)
        if job is None:
            return jsonify({"error": "job not found"}), 404
        if job["status"] != "done":
            return jsonify({"error": f"job is {job['status']}", "status": job["status"]}), 409
        return jsonify(job["result"])

    return app


def _with_strategy(settings, strategy):
    import copy
    s = copy.copy(settings)
    s.strategy = strategy
    return s


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
