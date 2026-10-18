"""Prompt strategies: the right text goes into the right prompt."""
from src import prompts
from src.summarize import MockClient, summarize, _parse_json, _parse_loose


def test_all_strategies_listed():
    assert set(prompts.STRATEGIES) == {"stuff", "map_reduce", "refine"}


def test_stuff_prompt_carries_transcript():
    p = prompts.stuff_prompt("hello world transcript")
    assert "hello world transcript" in p
    assert "summary" in p.lower()


def test_map_prompt_carries_chunk_and_time():
    p = prompts.map_prompt("some words", 65.0, 130.0)
    assert "some words" in p and "65" in p


def test_reduce_prompt_asks_for_json():
    p = prompts.reduce_prompt("--- Part 1 ---\n- point one")
    assert "JSON" in p and "summary" in p


def test_refine_prompt_carries_both():
    p = prompts.refine_prompt("old summary", "new chunk text")
    assert "old summary" in p and "new chunk text" in p


def test_summarize_all_strategies_with_mock():
    chunks = [
        {"text": "first part about cats", "start": 0.0, "end": 10.0, "words": 4},
        {"text": "second part about dogs", "start": 10.0, "end": 20.0, "words": 4},
    ]
    for strategy in prompts.STRATEGIES:
        result = summarize(chunks, strategy, MockClient())
        assert result["summary"], strategy
        assert "key_points" in result and "chapters" in result


def test_summarize_rejects_unknown_strategy():
    try:
        summarize([], "nope", MockClient())
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_parse_json_finds_object_in_noise():
    raw = 'Sure! Here it is:\n{"summary": "abc", "key_points": ["x"]}\nDone.'
    assert _parse_json(raw) == {"summary": "abc", "key_points": ["x"]}


def test_parse_loose_splits_bullets():
    raw = "This is the summary.\n\n- point one\n- point two"
    out = _parse_loose(raw)
    assert out["summary"] == "This is the summary."
    assert out["key_points"] == ["point one", "point two"]
