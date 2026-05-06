"""Tests for prompt construction (reply_generator + clone_test)."""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from clone_test import build_prompt as build_clone_test_prompt  # noqa: E402
from reply_generator import build_prompt, format_profile  # noqa: E402


def _load_example_profile() -> dict:
    path = os.path.join(ROOT, "examples", "founder_saas.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["profile"]


def test_format_profile_includes_signature_behaviors():
    profile = _load_example_profile()
    rendered = format_profile(profile)
    assert "Signature Behaviors" in rendered
    # Specific behaviors from the profile should appear verbatim in the prompt.
    for behavior in profile["signature_behaviors"]:
        assert behavior in rendered, f"Missing signature behavior in prompt: {behavior!r}"


def test_reply_prompt_contains_inputs():
    profile = _load_example_profile()
    prompt = build_prompt(
        profile=profile,
        incoming="How much for a website?",
        platform="email",
        goal="qualify",
    )
    assert "How much for a website?" in prompt
    assert "email" in prompt
    assert "qualify" in prompt
    # The schema shape must be in the prompt so the model returns valid JSON.
    assert "style_confidence" in prompt
    assert "intent" in prompt


def test_reply_prompt_handles_missing_goal():
    profile = _load_example_profile()
    prompt = build_prompt(profile=profile, incoming="hi")
    # No goal supplied — prompt should explicitly tell the model to infer it.
    assert "infer" in prompt.lower()


def test_clone_test_prompt_contains_both_messages():
    profile = _load_example_profile()
    prompt = build_clone_test_prompt(
        profile=profile,
        message_a="depends on what you're trying to do",
        message_b="I'd be happy to help! Let me know how I can assist.",
    )
    assert "depends on" in prompt
    assert "I'd be happy to help" in prompt
    # Must instruct the model to reference specific profile features.
    assert "specific" in prompt.lower()
