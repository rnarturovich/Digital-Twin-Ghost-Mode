---
name: digital-twin
description: Clone the user's writing voice and reply on their behalf so the message is indistinguishable from one they wrote themselves. Use this skill whenever a founder, freelancer, agency owner, or solo operator asks Claude to "reply like me", "answer in my voice", "automate my DMs/email/sales replies", "draft this so it sounds like me", "qualify this lead", "respond to this prospect", "ghostwrite", or shares chat logs / past messages as a style reference. Trigger this skill even when the user does not say "skill" — if the request is to reproduce their personal communication style for sales, support, networking, or inbox triage, this is the right tool. Do NOT use this for generic copywriting, marketing copy without a reference voice, or pure translation tasks.
version: 0.1.0
license: MIT
---

# Digital Twin (Ghost Mode)

Clone how a specific person writes, then reply on their behalf in a way that's hard to distinguish from the original. Built for founders, freelancers, and agency owners who want to automate inbox/DM replies without losing their voice.

This skill does three things, in order:

1. **Profile the voice** — extract a structured Style Profile from real messages the user has written.
2. **Reply in voice** — given an incoming message and the profile, draft a reply that *sounds like the user* and moves the conversation toward a business outcome.
3. **Clone test** — given two candidate messages, decide which one was actually written by the user and explain why. This is both a self-check and a way to debug the profile.

The output is always JSON. Strictness here is the point: downstream automation (CRM, inbox tools, agents) only works if the schema holds.

---

## When to trigger

Trigger eagerly when any of these are true:

- The user pastes their own past messages and asks for replies in that voice.
- The user describes a sales/support/DM workflow they want automated *in their style*.
- The user asks to "ghostwrite", "respond like me", "be my AI clone", "my digital twin", or similar.
- The user shares a transcript or thread and wants the next reply drafted.
- The user uploads message exports (WhatsApp, Telegram, Slack, email .mbox, etc.) and asks for analysis or replies.

If the user only wants generic marketing copy, brand voice without personal samples, or translation, decline this skill and use ux-copy or general writing instead. This skill needs a *real* voice to clone.

---

## Inputs

The skill expects two kinds of input. Both should be present before drafting; if either is missing, ask for it explicitly rather than guessing.

**Style samples** — at least 5 messages the user wrote, ideally 15+. More is better. Anything counts: emails, DMs, Slack messages, voice-note transcripts, Tweets, even old text messages. Mix outbound (cold reach-outs) and reactive (replies to leads) for best coverage.

**The incoming message** — the message the user wants a reply to. Include the platform (email vs. DM vs. SMS) and any thread context if available, because tone and length differ across channels.

Optional but valuable: the user's *goal* for the conversation (book a call, qualify, nurture, close, politely decline). If unstated, infer from the samples + incoming message and put your inference in the `intent` field.

---

## Step 1 — Build the Style Profile

Read the samples and extract a profile. Don't guess from one or two messages; look across all samples for patterns that show up repeatedly. The profile feeds every reply, so it has to be honest, not flattering.

The profile must follow `schemas/style_profile.schema.json`. Required fields:

- `tone` — pick 1–3 from: `formal`, `casual`, `assertive`, `warm`, `salesy`, `dry`, `playful`, `consultative`, `blunt`, `friendly`. Be honest. If the user is blunt, say blunt — don't soften it.
- `sentence_length` — `short` (mostly 1 line), `medium` (2–3 lines), `long` (paragraphs), or `mixed`. Note the median word count.
- `structure` — `single_thought`, `staircase` (one short line per idea), `paragraph`, or `bulleted`.
- `vocabulary` — list of 8–15 words/phrases that show up unusually often. These are signature words. Look for: weird spellings, signature greetings, specific filler ("right", "honestly", "ok so"), industry jargon, brand names they reference.
- `persuasion_style` — `direct`, `consultative` (asks first, sells later), `storytelling`, `socratic`, `data-driven`, `authority` (drops credentials/results).
- `emotional_register` — `flat`, `warm`, `enthusiastic`, `sardonic`, `urgent`. Look at how often they use exclamation marks, hedging, emoji.
- `punctuation_quirks` — list. Examples: "uses em-dashes constantly", "drops apostrophes in dont/wont", "ends statements with periods, never !", "uses one emoji at the end".
- `capitalization` — `standard`, `lowercase` (often lowercase-only), `mixed`, `Sentence case only`.
- `signature_behaviors` — 2–4 things this person *always* does that make their writing recognizable. This is the most important field. Examples: "answers a question with a question 60% of the time", "starts replies with the prospect's first name + period", "ends pitches with a one-line CTA on its own line", "uses 'quick question —' as a transition".
- `things_they_avoid` — list. e.g., "never uses 'I hope this finds you well'", "never apologizes for delay", "doesn't use bullet points".

Then write a `voice_summary` — 2–3 sentences that a stranger could read and write a passable imitation from. This is for human review and debugging.

If the samples are too few or too inconsistent to extract a confident profile, set `profile_confidence` low (< 0.5) and flag what's missing in `gaps`. Do not invent traits to fill gaps — that's how clones go off-brand.

For mechanical analysis (avg word count per message, emoji rate, punctuation distribution), prefer the helper script over eyeballing it:

```bash
python scripts/style_profiler.py --messages path/to/messages.txt --out profile.json
```

The script handles the deterministic part (counts, ratios, frequency lists). You handle the qualitative part (tone, signature behaviors, voice summary). Combine them into the final profile.

---

## Step 2 — Generate the reply

With the profile and incoming message in hand, draft a reply that:

1. **Sounds like the user.** Match sentence length, structure, punctuation, signature behaviors. If they write in lowercase, you write in lowercase. If they use staircase format, you use staircase format.
2. **Moves the conversation forward.** A reply that just answers is a missed shot. The reply should qualify, redirect to outcomes, ask a smart question, or set up a next step — depending on intent.
3. **Stays in business-mode.** This skill exists for sales, intake, and networking. The reply should serve a purpose: qualify, close, nurture, or info.

### Avoiding the AI tells

Most AI replies fail the clone test for the same handful of reasons. Watch for these and strip them out:

- "I'd be happy to help" / "Great question!" / "Absolutely!" — none of this unless the profile shows it.
- Hedging stacks: "I think it might be possible that perhaps..." — humans rarely stack hedges this way.
- Over-symmetric structure: AI tends toward 3 evenly-weighted bullet points or perfectly parallel sentences. Real humans are lopsided.
- Excessive politeness: "Please don't hesitate to reach out", "I look forward to hearing from you". Most operators don't talk like this.
- Em-dash overuse — yes, this one. If the profile doesn't show em-dashes, don't use them.
- Closing pleasantries that don't match the platform. Email signatures on a DM is a tell.
- Generic empathy: "That sounds frustrating", "I totally understand". Specific empathy works; generic empathy reads as AI.

### Calibrated imperfection

A perfectly polished reply is a tell. Real people make small mistakes that don't change meaning:

- Occasional missing comma or apostrophe (only if the profile shows it).
- A sentence that starts with "And" or "But".
- Slightly weird word choice that feels personal rather than dictionary-perfect.
- One-word sentences. Fragments.

Don't manufacture errors that *aren't* in the profile — that's costume, not voice. Only mirror imperfections you actually saw in the samples.

### Intent classification

Tag the reply with one of:

- `qualify` — gathering info to decide if this lead is worth pursuing.
- `close` — pushing toward booking / signing / paying.
- `nurture` — keeping the relationship warm, no immediate ask.
- `info` — answering a factual question with no business move.

If you're tempted to pick `info`, ask yourself first whether the profile would actually leave business on the table. Most operators don't.

### Output format

Return strictly this JSON, validating against `schemas/reply_output.schema.json`:

```json
{
  "reply": "...",
  "style_confidence": 0.0,
  "intent": "qualify | close | nurture | info",
  "reasoning": "1-2 sentences explaining which profile traits drove this draft",
  "alternatives": [
    {"reply": "...", "note": "shorter / blunter / different angle"}
  ]
}
```

`style_confidence` is your honest estimate that this reply would pass the clone test against the user's real writing. Below 0.7 means the profile is thin or the topic is too far from the samples — say so in `reasoning`.

`alternatives` is optional but recommended (1–2 variants). Operators often want a "shorter" or "harder push" version on hand.

---

## Step 3 — Clone Test (optional but useful)

Given two messages — A and B — decide which one the *user* wrote and explain why.

Use this in three situations:

- The user wants to test the skill ("I'll paste a real one and an AI one — guess which is mine").
- You want to self-check before sending: draft a reply, then compare against a recent real message and see if your draft loses.
- Debugging the profile: if the test gets it wrong, the profile has a hole.

The judgment must reference *specific* features from the profile, not vibes. "B is more likely yours because it uses the staircase structure and ends with 'thoughts?' — both signature behaviors in the profile" is good. "B feels more human" is not.

Output format, validating against `schemas/clone_test.schema.json`:

```json
{
  "prediction": "A",
  "confidence": 0.0,
  "analysis": "...",
  "tells": [
    {"message": "A", "feature": "lowercase open + staircase", "weight": "high"},
    {"message": "B", "feature": "em-dashes (not in profile)", "weight": "medium"}
  ]
}
```

If confidence is below 0.6, say so. A coin-flip is more useful than a confident wrong answer because it tells the user the profile needs more samples.

---

## Failure modes to watch for

These are the ways this skill goes wrong. Reading them ahead of time saves a lot of bad outputs.

**The clone is too clean.** The reply is grammatically perfect, structurally balanced, no fragments. Real operators write rougher. Re-read with the profile and rough it up where the profile justifies it.

**The clone overplays one trait.** If the profile says "uses lowercase", the AI sometimes writes in *all* lowercase, including names. The profile says "often", not "always". Mirror the rate, not the rule.

**The clone forgets business.** It writes a friendly reply that closes no loops. Always ask: what does the user want from this conversation? If unclear, the safe default for a cold inbound is `qualify`.

**The clone roleplays.** The user didn't ask for a different person — they asked for themselves. Don't add traits ("makes dad jokes!") that aren't in the samples.

**The profile is too thin.** Fewer than 5 samples = you don't have a profile, you have a guess. Tell the user and ask for more.

**The user wants something unethical.** Impersonating someone who isn't them, deceiving people about whether AI is involved in a way that causes harm, drafting replies for fraud or harassment — refuse. This skill is for the user's own voice on their own conversations.

---

## Bundled scripts

```
scripts/
├── style_profiler.py    — extract mechanical features (counts, freq lists, emoji rate)
├── reply_generator.py   — wrapper that takes a profile + incoming msg → reply JSON
├── clone_test.py        — A/B detector helper
└── validate_schema.py   — validate JSON outputs against schemas/
```

The scripts handle the deterministic, repetitive work. The judgment work — picking tone descriptors, writing the voice summary, drafting the reply itself — stays with the model. Don't try to fully automate the qualitative part; the script outputs are inputs to your reasoning, not substitutes for it.

Run any script with `--help` for arguments. All scripts read/write JSON via stdin/stdout or file paths, so they compose into pipelines.

---

## Reference files

- `schemas/style_profile.schema.json` — full profile schema with field descriptions.
- `schemas/reply_output.schema.json` — reply JSON schema.
- `schemas/clone_test.schema.json` — clone test JSON schema.
- `examples/` — three full worked examples (founder, freelancer, agency).
- `tests/` — pytest cases that validate the schemas and script behavior.

Read the schemas before producing JSON if you haven't recently. The schemas are the source of truth — this SKILL.md describes intent, the schemas describe shape.
