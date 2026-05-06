# Digital Twin (Ghost Mode)

> A Claude / Agent skill that clones how *you* write, then replies on your behalf in a way that's hard to tell from the real thing.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-18%20passing-brightgreen)](tests/)
[![Skill format](https://img.shields.io/badge/format-Anthropic%20Skill-blue)](SKILL.md)

Built for **founders, freelancers, and agency owners** who want to automate sales replies, DM intake, and inbox triage **without sounding like a chatbot**.

This is not a chatbot. It's a **personality + behavior cloning system** wired into a skill format that any Claude-compatible agent can pick up.

---

## What it does

```
        ┌─────────────────────┐
   you  │  15+ past messages  │
   ─►   │  (DMs, emails...)   │
        └──────────┬──────────┘
                   │
                   ▼
         ╔══════════════════╗      ┌──────────────────────┐
         ║  STEP 1          ║      │  StyleProfile.json   │
         ║  Profile voice   ║ ───► │  tone, signatures,   │
         ╚══════════════════╝      │  vocabulary, quirks  │
                                   └──────────┬───────────┘
                                              │
                  incoming msg ──────────────►│
                                              ▼
                                   ╔══════════════════╗
                                   ║  STEP 2          ║
                                   ║  Reply in voice  ║
                                   ╚══════════┬═══════╝
                                              ▼
                                   ┌──────────────────────┐
                                   │   reply.json         │
                                   │   (sounds like you)  │
                                   └──────────────────────┘
```

Three modes:

1. **Profile** — extracts a structured fingerprint from your past writing (tone, sentence length, signature behaviors, vocabulary, punctuation quirks).
2. **Reply** — given an incoming message + your profile, drafts a response that sounds like you and *moves the conversation forward* (qualifies, closes, nurtures).
3. **Clone Test** — given two candidate messages, predicts which one *you* wrote. Use it to debug your profile or as a fun party trick.

---

## Quick example

**Past messages from a SaaS founder:**

```
depends on what you're trying to do — most people who ask about pricing dont need pricing yet
quick question — are you actually shipping this week or is it a soft target?
honestly the v1 was wrong. shipped it monday, killed it wednesday.
the real issue isnt the dashboard, its that nobody trusts the numbers in it
```

**Incoming DM:**

> Hey! How much do you charge for a website?

**Generic AI reply (don't ship this):**

> I'd be happy to help! Our pricing varies depending on your needs. Could you tell me more about what you're looking for? I look forward to hearing from you!

**Digital Twin reply (looks like you wrote it):**

> depends on what you're actually trying to do — most people who ask me that dont need a website, they need leads.
>
> are you getting consistent inbound right now?

That's the difference. Same information, but one is unmistakably the founder, and the other is unmistakably a bot.

---

## Why this exists

Most "AI reply" tools either:

- write polished, generic, obviously-AI text that prospects screenshot and laugh at,
- or ask you to fill out a 30-question "brand voice questionnaire" and still sound off.

Neither works because **voice isn't a setting — it's the residue of how you actually write**. This skill works backwards from your real messages.

---

## Output is structured JSON

Every output validates against a schema. That means you can plug it straight into:

- a CRM ("auto-respond, but only if intent = qualify and confidence > 0.85"),
- an inbox triage agent,
- your own automation,
- a human-in-the-loop review queue.

```json
{
  "reply": "...",
  "style_confidence": 0.91,
  "intent": "qualify",
  "reasoning": "Used the signature opener, lowercase + dropped apostrophes, staircase structure, and the closing one-line question.",
  "alternatives": [
    {"reply": "...", "note": "shorter, blunter"}
  ]
}
```

Schemas live in [`schemas/`](schemas/).

---

## Install

This is a skill — drop the folder into your skills directory.

**Anthropic's Claude Code / Agent SDK / Cowork:**

```bash
# Clone and put it where your skills live
git clone https://github.com/<your-org>/digital-twin.git ~/.claude/skills/digital-twin
```

Then restart your client. The skill auto-triggers on prompts like *"reply like me"*, *"respond to this lead in my voice"*, *"draft this so it sounds like me"*.

**Manual / programmatic use** (no Claude wrapper required):

```bash
cd digital-twin
pip install jsonschema  # optional, for stricter validation
python scripts/style_profiler.py --messages your_messages.txt > profile_stats.json
python scripts/reply_generator.py --profile profile.json --incoming "How much for a website?" | claude -p
```

The scripts are pure prompt builders — they emit a fully-formed prompt to stdout that you can pipe into any model.

---

## Files

```
digital-twin/
├── SKILL.md                  # the core — what the model reads
├── schemas/                  # JSON schemas for profile, reply, clone-test
├── scripts/
│   ├── style_profiler.py     # mechanical features extractor
│   ├── reply_generator.py    # builds the reply prompt
│   ├── clone_test.py         # builds the A/B test prompt
│   └── validate_schema.py    # validates outputs against schemas
├── examples/                 # 3 worked examples (founder, freelancer, agency)
├── tests/                    # 18 pytest cases — all green
├── LICENSE                   # MIT
└── README.md                 # this file
```

---

## Tested archetypes

The bundled examples cover three voices that are very different from each other on purpose — if it works for these, it works for most operators:

| Archetype | Voice signature |
|---|---|
| SaaS founder | Lowercase, blunt, redirects to qualifying questions |
| Freelance designer | Warm, storytelling, asks for the backstory before pricing |
| Performance marketing agency | Authority + hard numbers, proposes specific calendar slots |

Read [`examples/`](examples/) for full profiles + sample replies.

---

## Anti-AI-tells checklist

The skill ships with explicit guardrails for the most common ways AI replies get caught. The model is instructed to strip:

- "I'd be happy to help" / "Great question!" / "Absolutely!"
- Stacked hedging ("I think it might be possible that perhaps...")
- Over-symmetric structure (perfectly parallel bullets)
- Em-dashes when not in your profile (yes, the AI giveaway)
- Generic empathy ("That sounds frustrating")
- Email sign-offs on a DM
- Vocabulary you'd never actually use

It also calibrates *imperfection* — fragments, missing apostrophes, lowercase — but only at the rate they actually appear in your samples. A perfectly polished reply is a tell.

---

## Run the tests

```bash
pip install pytest
pytest tests/ -v
```

All 18 tests should pass. They cover schema validity, prompt construction, and the mechanical-features extractor.

---

## Roadmap

- [ ] Multilingual profiles (Spanish, Russian, Portuguese — same architecture, different stopword lists)
- [ ] Channel-specific sub-profiles (your DM voice ≠ your email voice)
- [ ] Drift detection (alert when generated replies start looking less like you)
- [ ] CRM connectors (HubSpot, Pipedrive, Attio) for direct write-back
- [ ] Reverse mode — Style Auditor: detect AI-generated messages in your inbox

PRs welcome.

---

## Ethics

This skill is meant for **your own voice** on **your own conversations**. It's not for impersonating other people, deceiving counterparties about whether AI is involved in a way that could harm them, or drafting replies for fraud or harassment. The skill itself refuses these uses; please don't try to work around it.

If you're using this commercially with prospects, consider disclosing AI assistance in line with your local advertising and consumer protection rules.

---

## License

MIT. Build whatever you want with it. Stars appreciated 🌟
