#!/usr/bin/env python3
"""
style_profiler.py
=================

Extract the *mechanical* features of a writing style from a list of messages.

The qualitative part of a Style Profile (tone, signature behaviors, voice
summary) needs human/model judgment. This script handles only the parts that
are mechanical and deterministic — counts, ratios, frequency lists — so the
model can spend its tokens on the parts that actually require thinking.

USAGE
-----

    python style_profiler.py --messages messages.txt --out stats.json

    # Or via stdin:
    cat messages.txt | python style_profiler.py --stdin

INPUT FORMAT
------------

Plain text file with ONE MESSAGE PER PARAGRAPH. Messages are separated by one
or more blank lines. Whitespace inside a message is preserved.

OUTPUT
------

JSON object matching the `stats` sub-schema in style_profile.schema.json,
plus a `top_phrases` field (uni/bi/tri-grams the user uses unusually often)
and a `punctuation_distribution` field.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from statistics import mean, median
from typing import List

# A coarse emoji range — covers the common cases. Not every codepoint, but
# the false-negative rate on real chat messages is low enough.
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F6FF"   # symbols & pictographs, transport
    "\U0001F700-\U0001F77F"   # alchemical
    "\U0001F900-\U0001F9FF"   # supplemental symbols and pictographs
    "\U0001FA70-\U0001FAFF"   # symbols and pictographs extended-A
    "\U00002600-\U000026FF"   # misc symbols
    "\U00002700-\U000027BF"   # dingbats
    "]",
    flags=re.UNICODE,
)

WORD_RE = re.compile(r"[A-Za-z']+")
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "to",
    "of", "in", "on", "at", "for", "with", "by", "from", "as", "that", "this",
    "it", "its", "i", "you", "we", "they", "he", "she", "him", "her", "them",
    "my", "your", "our", "their", "me", "us", "so", "not", "no", "yes",
    "will", "would", "can", "could", "should", "just", "about", "what",
    "when", "where", "how", "why", "who",
}


def split_messages(text: str) -> List[str]:
    """Split a text blob into messages on blank lines. Trim whitespace."""
    blocks = re.split(r"\n\s*\n", text.strip())
    return [b.strip() for b in blocks if b.strip()]


def word_count(msg: str) -> int:
    return len(WORD_RE.findall(msg))


def emoji_count(msg: str) -> int:
    return len(EMOJI_RE.findall(msg))


def is_all_lowercase(msg: str) -> bool:
    """True if the message has no uppercase letters at all (and at least one letter)."""
    has_letter = any(c.isalpha() for c in msg)
    return has_letter and msg == msg.lower()


def ngrams(tokens: List[str], n: int) -> List[str]:
    return [" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def top_phrases(messages: List[str], top_k: int = 12) -> List[str]:
    """
    Return phrases that look distinctive for this writer.

    We pull the top uni-, bi-, and tri-grams excluding stopword-only n-grams
    and very short tokens, then merge into a single ranked list. This is a
    cheap proxy — for production use you'd compare against a reference corpus
    to surface phrases that are over-represented relative to baseline. Here
    we trust frequency + a stopword filter, which is fine for a starter.
    """
    all_unigrams = []
    all_bigrams = []
    all_trigrams = []

    for msg in messages:
        tokens = [t.lower() for t in WORD_RE.findall(msg)]
        all_unigrams.extend([t for t in tokens if len(t) >= 3 and t not in STOPWORDS])
        bigrams = ngrams(tokens, 2)
        all_bigrams.extend(
            bg for bg in bigrams
            if not all(part in STOPWORDS for part in bg.split())
        )
        trigrams = ngrams(tokens, 3)
        all_trigrams.extend(
            tg for tg in trigrams
            if not all(part in STOPWORDS for part in tg.split())
        )

    uni = Counter(all_unigrams).most_common(top_k)
    bi = Counter(all_bigrams).most_common(top_k)
    tri = Counter(all_trigrams).most_common(top_k // 2)

    # Prefer multi-word phrases when frequencies are close — they're more
    # distinctive than single common words.
    combined: List[tuple] = []
    combined.extend((phrase, count, 3) for phrase, count in tri if count >= 2)
    combined.extend((phrase, count, 2) for phrase, count in bi if count >= 2)
    combined.extend((phrase, count, 1) for phrase, count in uni if count >= 2)

    combined.sort(key=lambda x: (-x[1], -x[2]))
    seen = set()
    out = []
    for phrase, _count, _n in combined:
        # Drop phrases fully contained in a phrase we already kept.
        if any(phrase in s and phrase != s for s in seen):
            continue
        seen.add(phrase)
        out.append(phrase)
        if len(out) >= top_k:
            break
    return out


def punctuation_distribution(messages: List[str]) -> dict:
    counts = Counter()
    total_chars = 0
    for msg in messages:
        total_chars += len(msg)
        for ch in msg:
            if ch in ".,!?;:—–-…":
                counts[ch] += 1
    if total_chars == 0:
        return {}
    return {ch: round(c / total_chars, 5) for ch, c in counts.items()}


def profile_messages(messages: List[str]) -> dict:
    if not messages:
        raise ValueError("No messages provided. Need at least 1.")

    word_counts = [word_count(m) for m in messages]
    emoji_counts = [emoji_count(m) for m in messages]
    exclamations = [m.count("!") for m in messages]
    questions = [m.count("?") for m in messages]
    lowercase_msgs = [is_all_lowercase(m) for m in messages]

    return {
        "sample_count": len(messages),
        "median_word_count": round(median(word_counts), 2),
        "mean_word_count": round(mean(word_counts), 2),
        "emoji_rate": round(mean(emoji_counts), 4),
        "exclamation_rate": round(mean(exclamations), 4),
        "question_rate": round(mean(questions), 4),
        "lowercase_ratio": round(sum(lowercase_msgs) / len(messages), 4),
        "top_phrases": top_phrases(messages),
        "punctuation_distribution": punctuation_distribution(messages),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--messages", help="Path to a text file with one message per paragraph.")
    src.add_argument("--stdin", action="store_true", help="Read messages from stdin.")
    parser.add_argument("--out", help="Write JSON output to this file (default: stdout).")
    args = parser.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    else:
        with open(args.messages, "r", encoding="utf-8") as f:
            text = f.read()

    messages = split_messages(text)
    if not messages:
        print("No messages found. Separate messages with blank lines.", file=sys.stderr)
        return 2

    result = profile_messages(messages)
    payload = json.dumps(result, indent=2, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload)
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
