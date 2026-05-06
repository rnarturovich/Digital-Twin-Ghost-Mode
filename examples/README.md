# Examples

Three full worked examples spanning the target audiences for this skill. Each
file contains:

1. A complete `profile` matching `schemas/style_profile.schema.json`
2. An `incoming_message` (the lead's question)
3. A `reply_output` matching `schemas/reply_output.schema.json`

Use them as:

- **Few-shot prompts** when calling the model. Pass one or two examples in
  the prompt to anchor the format and the style.
- **Test fixtures** for the schema validator and the test suite.
- **Reference reading** when you're not sure how blunt or warm a profile
  should look. Compare against the closest archetype.

| File | Archetype | Voice in one line |
|---|---|---|
| `founder_saas.json` | SaaS founder | Lowercase, blunt, redirects to qualifying questions |
| `freelancer_designer.json` | Brand designer | Warm, storytelling, asks for the backstory before pricing |
| `agency_owner.json` | Performance marketing agency | Authority + numbers, proposes specific calendar slots |

`sample_messages_founder.txt` is a raw text file (one message per paragraph)
matching the founder profile. Feed it into `style_profiler.py` to see the
mechanical-features extraction in action:

```bash
python ../scripts/style_profiler.py --messages sample_messages_founder.txt
```

The output of that command is the `stats` block + a phrase list — the
deterministic part of the profile. The qualitative fields (tone, signature
behaviors, voice summary) require the model's judgment on top.
