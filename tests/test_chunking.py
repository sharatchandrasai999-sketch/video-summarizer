"""Chunking: long transcripts split into bounded, overlapping chunks."""
from src.chunking import chunk_segments


def _segs(n, words_each=50):
    return [
        {"start": float(i), "end": float(i + 1), "text": "word " * words_each}
        for i in range(n)
    ]


def test_chunks_respect_max_words():
    chunks = chunk_segments(_segs(10), max_words=120, overlap_words=0)
    assert len(chunks) > 1
    for c in chunks:
        assert c["words"] <= 120


def test_overlap_keeps_tail_words():
    chunks = chunk_segments(_segs(6), max_words=120, overlap_words=60)
    assert len(chunks) >= 2
    # second chunk starts before the first one ends (overlap, not a gap)
    assert chunks[1]["start"] < chunks[0]["end"]


def test_timestamps_cover_full_range():
    segs = _segs(8)
    chunks = chunk_segments(segs, max_words=200, overlap_words=0)
    assert chunks[0]["start"] == 0.0
    assert chunks[-1]["end"] == 8.0


def test_short_transcript_is_one_chunk():
    chunks = chunk_segments(_segs(2), max_words=1200)
    assert len(chunks) == 1
