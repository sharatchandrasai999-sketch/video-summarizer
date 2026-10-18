"""Split a long transcript into chunks the LLM can handle at once.

Chunks are built from whole whisper segments (never cut mid-sentence),
with a small word overlap so ideas at the edges are not lost.
"""


def chunk_segments(segments, max_words: int = 1200, overlap_words: int = 100):
    chunks = []
    current, current_words = [], 0

    for seg in segments:
        words = seg["text"].split()
        if current and current_words + len(words) > max_words:
            chunks.append(_pack(current))
            # keep the tail of this chunk as overlap for the next one
            tail, tail_words = [], 0
            for s in reversed(current):
                w = len(s["text"].split())
                if tail_words + w > overlap_words:
                    break
                tail.insert(0, s)
                tail_words += w
            current, current_words = tail, tail_words
        current.append(seg)
        current_words += len(words)

    if current:
        chunks.append(_pack(current))
    return chunks


def _pack(segments):
    text = " ".join(s["text"] for s in segments)
    return {
        "text": text,
        "start": segments[0]["start"],
        "end": segments[-1]["end"],
        "words": len(text.split()),
    }
