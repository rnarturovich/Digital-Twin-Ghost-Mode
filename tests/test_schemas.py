"""Tests that the bundled examples validate against the bundled schemas."""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCHEMAS_DIR = os.path.join(ROOT, "schemas")
EXAMPLES_DIR = os.path.join(ROOT, "examples")
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from validate_schema import validate  # noqa: E402


def _load(p: str) -> dict:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def test_profile_schema_loads():
    schema = _load(os.path.join(SCHEMAS_DIR, "style_profile.schema.json"))
    assert schema["title"] == "StyleProfile"


def test_reply_schema_loads():
    schema = _load(os.path.join(SCHEMAS_DIR, "reply_output.schema.json"))
    assert schema["title"] == "ReplyOutput"


def test_clone_test_schema_loads():
    schema = _load(os.path.join(SCHEMAS_DIR, "clone_test.schema.json"))
    assert schema["title"] == "CloneTestResult"


def test_all_example_profiles_validate():
    """Every bundled example's `profile` field must match the profile schema."""
    schema = _load(os.path.join(SCHEMAS_DIR, "style_profile.schema.json"))
    for fname in ("founder_saas.json", "freelancer_designer.json", "agency_owner.json"):
        example = _load(os.path.join(EXAMPLES_DIR, fname))
        errors = validate(example["profile"], schema)
        assert not errors, f"{fname} profile failed: {errors}"


def test_all_example_replies_validate():
    """Every bundled example's `reply_output` must match the reply schema."""
    schema = _load(os.path.join(SCHEMAS_DIR, "reply_output.schema.json"))
    for fname in ("founder_saas.json", "freelancer_designer.json", "agency_owner.json"):
        example = _load(os.path.join(EXAMPLES_DIR, fname))
        errors = validate(example["reply_output"], schema)
        assert not errors, f"{fname} reply failed: {errors}"


def test_invalid_reply_is_caught():
    """Sanity check: an invalid reply should produce errors."""
    schema = _load(os.path.join(SCHEMAS_DIR, "reply_output.schema.json"))
    bad = {
        "reply": "",  # minLength 1, empty fails
        "style_confidence": 1.5,  # out of range
        "intent": "definitely_not_an_intent",  # not in enum
        "reasoning": "short",  # below minLength
    }
    errors = validate(bad, schema)
    assert errors, "Expected validation errors for clearly bad reply"
    # The errors list should mention several distinct problems.
    assert len(errors) >= 3, errors


def test_clone_test_result_validates():
    schema = _load(os.path.join(SCHEMAS_DIR, "clone_test.schema.json"))
    good = {
        "prediction": "B",
        "confidence": 0.82,
        "analysis": "B uses lowercase open and ends with a one-line question — both signature behaviors.",
        "tells": [
            {"message": "B", "feature": "lowercase open", "weight": "high"},
            {"message": "A", "feature": "em-dashes not in profile", "weight": "medium"},
        ],
    }
    errors = validate(good, schema)
    assert not errors, errors
