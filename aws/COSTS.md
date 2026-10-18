# What the AWS GPU box costs (read this before you launch anything)

Prices are on-demand, Linux, us-east-1. AWS changes prices, so check the
console before you launch. You pay for every hour the box is ON, even idle.
Stop it when you are done.

| Box | GPU | GPU memory | ~$/hour | Good for |
|---|---|---|---|---|
| g4dn.xlarge | 1x T4 | 16 GB | $0.53 | Whisper only (fast transcription) |
| g5.xlarge | 1x A10G | 24 GB | $1.01 | Whisper + API; Mixtral does NOT fit |
| g5.12xlarge | 4x A10G | 96 GB | ~$5.67 | Whisper + Mixtral 8x7B (4-bit) via vLLM |

## Why Mixtral needs the big box

Mixtral 8x7B has 46.7 billion parameters.

- Full precision: ~93 GB of GPU memory. Fits almost nowhere cheap.
- 4-bit compressed (AWQ): ~25 GB for the weights + room for context.
  That is why the deploy script uses a 4-bit model on g5.12xlarge
  (96 GB total across 4 GPUs).

A single g5.xlarge (24 GB) cannot hold Mixtral, even compressed, once you
add context memory. Do not try; it will crash with out-of-memory.

## The free path (recommended while learning)

- Whisper `small` on your laptop CPU: fine for short clips.
- Mixtral through the Groq API free tier: no GPU bill at all.
  Set `LLM_BACKEND=groq` and add your free key.

A 10-minute video costs roughly: $0.17 of g5.xlarge time for Whisper,
plus $0 for Groq. The full Mixtral-on-GPU box only makes sense when you
summarize videos all day, every day.
