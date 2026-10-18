"""Prompt strategies: three ways to turn a long transcript into a summary.

- stuff:      put the whole transcript in one prompt. Simple and fast,
              but only works for short videos (the model has a size limit).
- map_reduce: summarize each chunk on its own ("map"), then combine those
              small summaries into one final summary ("reduce"). Best for
              long videos.
- refine:     write a summary of the first chunk, then read each next chunk
              and improve the summary step by step. Keeps one flowing story.
"""

SYSTEM = (
    "You are a helpful assistant that writes clear video summaries. "
    "Use short sentences and plain words. Never invent facts that are not "
    "in the transcript."
)

STRATEGIES = ("stuff", "map_reduce", "refine")


def stuff_prompt(transcript: str) -> str:
    return (
        "Summarize this video transcript.\n"
        "First write a summary of 5-8 sentences.\n"
        "Then write a blank line and 5-8 key points, one per line starting with '-'.\n\n"
        f"TRANSCRIPT:\n{transcript}"
    )


def map_prompt(chunk_text: str, chunk_start: float, chunk_end: float) -> str:
    return (
        f"This is part of a video transcript (from {int(chunk_start)}s to {int(chunk_end)}s).\n"
        "Write 3-5 short bullet points of the key ideas in this part. "
        "Keep each point under 20 words. Start each line with '-'.\n\n"
        f"PART:\n{chunk_text}"
    )


def reduce_prompt(chunk_summaries: str) -> str:
    return (
        "You are given bullet-point summaries of each part of a video.\n"
        "Write one final summary. Reply with JSON only, exactly these keys:\n"
        '{"summary": "5-8 sentences", '
        '"key_points": ["5-8 short bullets"], '
        '"chapters": [{"title": "short title", "part": 1}]}\n\n'
        f"PART SUMMARIES:\n{chunk_summaries}"
    )


def refine_prompt(existing_summary: str, chunk_text: str) -> str:
    return (
        "Here is the summary of a video so far:\n"
        f"{existing_summary}\n\n"
        "Now read the next part of the transcript and improve the summary. "
        "Add new facts, fix anything wrong, keep it under 200 words.\n\n"
        f"NEXT PART:\n{chunk_text}"
    )
