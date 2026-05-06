"""Tests for the mechanical features extracted by style_profiler.py."""

from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from style_profiler import (  # noqa: E402
    is_all_lowercase,
    profile_messages,
    split_messages,
    top_phrases,
    word_count,
)


def test_split_on_blank_lines():
    text = "first message\n\nsecond message\n\n\nthird message"
    msgs = split_messages(text)
    assert msgs == ["first message", "second message", "third message"]


def test_split_handles_empty_input():
    assert split_messages("") == []
    assert split_messages("   \n   ") == []


def test_word_count_basic():
    assert word_count("hello world") == 2
    assert word_count("don't go") == 2  # contractions count as one word
    assert word_count("") == 0


def test_lowercase_detection():
    assert is_all_lowercase("hello world")
    assert is_all_lowercase("dont overthink it")
    assert not is_all_lowercase("Hello world")
    assert not is_all_lowercase("HELLO")
    # No letters at all = not lowercase (ambiguous, we say False)
    assert not is_all_lowercase("123 !!!")


def test_top_phrases_surfaces_repeated_distinctive_phrases():
    messages = [
        "depends on what you're trying to do",
        "depends on what you're trying to do here",
        "depends on the budget",
        "the real issue is leads",
        "the real issue is the offer",
    ]
    phrases = top_phrases(messages, top_k=10)
    # The repeated multi-word phrases should bubble up.
    assert any("depends on" in p for p in phrases), phrases
    assert any("real issue" in p for p in phrases), phrases


def test_profile_messages_full_pipeline():
    messages = [
        "depends on what you're trying to do — most people dont need that.",
        "honestly, depends on the goal. whats the actual problem?",
        "are you actually shipping or just exploring?",
        "fwiw I'd skip it. the math doesnt work.",
        "quick question — is this for v1 or the rebuild?",
    ]
    out = profile_messages(messages)
    assert out["sample_count"] == 5
    assert out["median_word_count"] > 0
    assert 0 <= out["lowercase_ratio"] <= 1
    assert "top_phrases" in out
    assert isinstance(out["top_phrases"], list)
    assert "punctuation_distribution" in out


def test_profile_handles_emoji():
    messages = ["love this 🔥🔥", "ok 👍", "no emoji here"]
    out = profile_messages(messages)
    # 3 emoji across 3 messages = 1.0 average
    assert out["emoji_rate"] == 1.0
