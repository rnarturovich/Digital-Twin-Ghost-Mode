#!/usr/bin/env python3
"""
reply_generator.py
==================

Compose the prompt the model needs to generate a reply in the user's voice.

This script does NOT call any LLM itself. It builds a single, well-structured
prompt string that you can pipe into your model of choice (Claude API,
OpenAI, local models — whatever). The actual draft is the model's job; this
script's job is to package the inputs consistently so every reply uses the
same instructions and the schema is enforced uniformly.

USAGE
-----

    python reply_generator.py \\
        --profile profile.json \\
        --incoming "How much for a website?" \\
        --platform email \\
        --goal qualify

    # Pipe the prompt into Claude:
    python reply_generator.py --profile p.json --incoming "..." | claude -p

OUTPUT
------

A single text prompt printed to stdout. Inside it, the model is asked to
return JSON matching `schemas/reply_output.schema.json`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from typing import Optional

PROMPT_TEMPLATE = """\
You are drafting a reply on behalf of a real person. The goal is to write something
indistinguishable from a message they wrote themselves. Match their voice, do not
roleplay as someone else, and move the conversation toward a business outcome.

# Style profile
{profile_block}

# Incoming message
Platform: {platform}
{thread_context}

> {incoming}

# User's stated goal
{goal}

# Hard rules
- Match sentence length, structure, capitalization, and signature behaviors from the profile.
- Do not invent traits not in the profile.
- Avoid AI tells: "I'd be happy to help", "Great question", stacked hedging, perfectly
  symmetric structure, em-dashes if not in the profile, generic empathy, generic sign-offs.
- Mirror the imperfections that show up in the profile (lowercase, fragments, missing
  apostrophes) at roughly the rate they appear. Do not manufacture errors that aren't there.
- The reply should advance the conversation: qualify, redirect to outcomes, ask a smart
  question, or set up a next step. Pure information-only replies are a last resort.

# Output
Return JSON only, matching this shape exactly:

{{
  "reply": "...",
  "style_confidence": 0.0,
  "intent": "qualify | close | nurture | info",
  "reasoning": "1-2 sentences explaining which profile traits drove this draft",
  "alternatives": [
    {{"reply": "...", "note": "shorter / blunter / different angle"}}
  ]
}}

Be honest about style_confidence. Below 0.7 means the profile is thin or the topic is
far from the samples — note that in `reasoning`. Include 1-2 alternatives if the choice
of angle is non-obvious.
"""


def format_profile(profile: dict) -> str:
    """Render the profile in a human-readable block for the prompt."""
    lines = []
    for key in [
        "tone",
        "sentence_length",
        "structure",
        "persuasion_style",
        "emotional_register",
        "capitalization",
        "vocabulary",
        "punctuation_quirks",
        "signature_behaviors",
        "things_they_avoid",
        "voice_summary",
    ]:
        if key not in profile:
            continue
        value = profile[key]
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            rendered = "\n".join(f"  - {item}" for item in value)
            lines.append(f"{label}:\n{rendered}")
        else:
            lines.append(f"{label}: {value}")
    if "stats" in profile:
        stats = profile["stats"]
        relevant = {k: stats[k] for k in stats if k in (
            "median_word_count", "emoji_rate", "exclamation_rate",
            "question_rate", "lowercase_ratio", "sample_count",
        )}
        lines.append(f"Stats: {json.dumps(relevant)}")
    return "\n".join(lines)


def build_prompt(
    profile: dict,
    incoming: str,
    platform: str = "unspecified",
    goal: Optional[str] = None,
    thread_context: Optional[str] = None,
) -> str:
    profile_block = format_profile(profile)
    return PROMPT_TEMPLATE.format(
        profile_block=profile_block,
        platform=platform,
        thread_context=f"Thread context: {thread_context}" if thread_context else "Thread context: (none)",
        incoming=incoming.strip(),
        goal=goal or "(not stated — infer from profile + incoming and put your inference in `intent`)",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", required=True, help="Path to a Style Profile JSON.")
    parser.add_argument("--incoming", required=True, help="The incoming message text (or @path/to/file).")
    parser.add_argument("--platform", default="unspecified", help="email | dm | sms | slack | other")
    parser.add_argument("--goal", default=None, help="qualify | close | nurture | info | (free text)")
    parser.add_argument("--thread", default=None, help="Optional thread context string or @path/to/file.")
    args = parser.parse_args()

    with open(args.profile, "r", encoding="utf-8") as f:
        profile = json.load(f)

    incoming = args.incoming
    if incoming.startswith("@"):
        with open(incoming[1:], "r", encoding="utf-8") as f:
            incoming = f.read()

    thread = args.thread
    if thread and thread.startswith("@"):
        with open(thread[1:], "r", encoding="utf-8") as f:
            thread = f.read()

    prompt = build_prompt(
        profile=profile,
        incoming=incoming,
        platform=args.platform,
        goal=args.goal,
        thread_context=thread,
    )
    print(prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
