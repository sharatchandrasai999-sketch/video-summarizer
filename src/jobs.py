"""Tiny job store: one JSON file per job, so jobs survive a restart."""
import json
import os
import time
import uuid


class JobStore:
    def __init__(self, path: str):
        os.makedirs(path, exist_ok=True)
        self.path = path

    def _file(self, job_id: str) -> str:
        return os.path.join(self.path, job_id + ".json")

    def create(self, filename: str, strategy: str) -> str:
        job_id = uuid.uuid4().hex[:12]
        data = {
            "job_id": job_id,
            "filename": filename,
            "strategy": strategy,
            "status": "queued",   # queued -> extracting -> transcribing -> summarizing -> done | failed
            "progress": 0,
            "created_at": time.time(),
            "error": None,
            "result": None,
        }
        self._write(job_id, data)
        return job_id

    def update(self, job_id: str, **fields):
        data = self.get(job_id)
        data.update(fields)
        self._write(job_id, data)

    def get(self, job_id: str):
        path = self._file(job_id)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return json.load(f)

    def _write(self, job_id: str, data: dict):
        tmp = self._file(job_id) + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, self._file(job_id))
