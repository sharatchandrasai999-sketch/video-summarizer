"""Pull the audio track out of a video file so Whisper can read it."""
import os
import subprocess


def extract_audio(video_path: str, out_path: str) -> str:
    """Convert video -> 16kHz mono wav. Raises if ffmpeg fails."""
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",               # drop the video, keep audio only
        "-ac", "1",          # mono
        "-ar", "16000",      # 16 kHz, what Whisper expects
        "-c:a", "pcm_s16le",
        out_path,
    ]
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr[-500:]}")
    return out_path
