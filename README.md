# Video Summarizer

Upload a video. Get back a written summary and key points.

It works in four steps. First it pulls the audio out of the video.
Then Whisper (a speech-to-text model) turns the audio into words.
Then the words are cut into small chunks.
Last, an LLM reads the chunks and writes the summary.

## Run it free on your laptop

You need Python 3.10+ and ffmpeg.

```bash
cd video-summarizer
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
cp .env.example .env
./venv/bin/python -m pytest tests/ -q   # 24 tests, no GPU needed
./venv/bin/python src/app.py            # opens on http://localhost:5000
```

Open http://localhost:5000 in your browser. Upload a video. Done.
The default settings use a mock writer, so you can test the full flow
with no model downloads and no API keys.

## Use real AI for free

Two free upgrades, no GPU box needed:

1. Better speech-to-text: in `.env`, keep `WHISPER_DEVICE=cpu` and set
   `WHISPER_MODEL=small` (or `base` for slower laptops).
2. Real summaries for free: get a free key at console.groq.com, then set
   `LLM_BACKEND=groq` and `GROQ_API_KEY=your-key` in `.env`.

Groq runs open models on their hardware. You pay nothing on the free tier.
Note: Groq retired Mixtral and keeps Llama 3.3 for enterprise customers,
so the free default is `openai/gpt-oss-120b` (checked live against Groq).
Mixtral is still the model for the self-hosted vLLM path on a GPU box.

## The API

```bash
# start a job (returns a job_id)
curl -X POST -F "file=@talk.mp4" -F "strategy=map_reduce" http://localhost:5000/api/jobs

# check progress: queued -> extracting -> transcribing -> summarizing -> done
curl http://localhost:5000/api/jobs/<job_id>

# get the summary when done
curl http://localhost:5000/api/jobs/<job_id>/result
```

The result has `summary`, `key_points`, `chapters`, `transcript`,
and the word-by-word `segments` with timestamps.

## The three prompt plans

Long videos do not fit in one prompt. So there are three plans:

- **stuff** — put the whole transcript in one prompt. Simple and fast.
  Only for short videos.
- **map_reduce** — summarize each chunk alone, then merge the small
  summaries into one final summary. Best for long videos.
- **refine** — summarize the first chunk, then read each next chunk and
  improve the summary step by step. Gives one smooth story.

Pick one per upload with the `strategy` field. The default is `map_reduce`.

## Run it on a GPU box (AWS, costs money)

Read `aws/COSTS.md` first. A GPU box bills every hour it is on.

- `g5.xlarge` (~$1.01/hr): fast Whisper, but Mixtral does not fit.
- `g5.12xlarge` (~$5.67/hr): fits Mixtral 8x7B (4-bit) plus Whisper.

To launch: set your key pair, security group, and subnet, then run
`bash aws/deploy.sh`. The box installs Docker, starts Mixtral with vLLM
(a fast model server), and starts the API. Stop the box when you are
done or it keeps billing.

## Project map

```
config.py            all settings (from environment variables)
src/app.py           the Flask API
src/pipeline.py      the 4-step flow: audio -> words -> chunks -> summary
src/audio.py         video -> audio (ffmpeg)
src/transcribe.py    audio -> words (Whisper)
src/chunking.py      words -> small chunks
src/summarize.py     chunks -> summary (3 backends: mock, Groq, vLLM)
src/prompts.py       the three prompt plans
src/jobs.py          job tracking (one JSON file per job)
tests/               24 tests, run with no GPU
Dockerfile           GPU-ready image
aws/                 launch scripts + cost notes
```
