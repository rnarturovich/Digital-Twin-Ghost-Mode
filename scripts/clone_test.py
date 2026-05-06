#!/usr/bin/env python3
"""
clone_test.py
=============

Build the prompt for an A/B "clone test" — given two candidate messages, the
model must decide which one was written by the user, and explain why using
specific features from the Style Profile.

Like reply_generator.py, this script does not call any LLM. It just packages
the inputs into a consistent prompt that returns JSON matching
`schemas/clone_test.schema.json`.

USAGE
-----

    python clone_test.py --profile profile.json --message-a "..." --message-b "..."

INTERPRETING THE OUTPUT
-----------------------

- High confidence + correct prediction = the profile is working.
- High confidence + WRONG prediction = the profile has a hole; the model is
  confidently keying on something that isn't actually a tell.
- Low confidence (< 0.6) = you don't have enough samples yet. Get more.

Use this regularly during onboarding (when the user is first feeding samples)
to debug the profile before you trust it for outbound automation.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from reply_generator import format_profile  # type: ignore

PROMPT_TEMPLATE = """\
You are testing a Style Profile. Two candidate messages are below. Exactly one
was written by the real person whose profile is shown. The other is a draft
written by an AI trying to imitate them.

# Style profile
{profile_block}

# Candidates

A:
{message_a}

B:
{message_b}

# Task
Decide which message — A or B — was written by the real person. Reference
*specific* features from the profile. "It feels more human" is not an answer;
"B uses the staircase structure and ends with a question — both signature
behaviors in the profile" is.

If both messages match the profile equally well or there's no real signal,
predict "tie" and set confidence below 0.6.

# Output
Return JSON only, matching this shape:

{{
  "prediction": "A | B | tie",
  "confidence": 0.0,
  "analysis": "1-3 sentences",
  "tells": [
    {{"message": "A", "feature": "specific observed feature", "weight": "low | medium | high"}}
  ]
}}
"""


def build_prompt(profile: dict, message_a: str, message_b: str) -> str:
    return PROMPT_TEMPLATE.format(
        profile_block=format_profile(profile),
        message_a=message_a.strip(),
        message_b=message_b.strip(),
    )


def _read_arg(value: str) -> str:
    """If value starts with @, read it as a path. Otherwise return as-is."""
    if value.startswith("@"):
        with open(value[1:], "r", encoding="utf-8") as f:
            return f.read()
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--message-a", required=True, help="Message A text or @path/to/file.")
    parser.add_argument("--message-b", required=True, help="Message B text or @path/to/file.")
    args = parser.parse_args()

    with open(args.profile, "r", encoding="utf-8") as f:
        profile = json.load(f)

    prompt = build_prompt(
        profile=profile,
        message_a=_read_arg(args.message_a),
        message_b=_read_arg(args.message_b),
    )
    print(prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
