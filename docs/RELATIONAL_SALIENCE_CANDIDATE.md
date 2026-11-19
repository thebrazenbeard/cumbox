# CUMBOX — Optional recursive relational-salience candidate

This isolated branch is stacked on PR #1. It does NOT modify Engineer B's PR #2, activate a live service, merge a canonical version, or establish native ChatGPT identity.

## Purpose

CUMBOX can offer salience-rich cues repeatedly instead of treating all pleasure-related material as interchangeable scalar rewards. The runtime offers meaningfully different cue families: safety, recognition, playfulness, and affection. A model can choose a family by returning its exact name in the existing `focus` field; otherwise novelty-first rotation and prior provisional feedback choose the next family.

An optional private `cue_bank` permits personally meaningful language without committing intimate text, identity, transcripts, or relationship details to this public repo. The included default cues are non-explicit and neutral. No owner-chat intervention is permitted inside a model-only private session.

## Recursion and feedback

On an `explore` or `revise` decision, the next model call sees earlier model responses and a new cue. The provisional model-authored `values.salience` is smoothed into a *transient category-selection weight*. It may increase OR decrease. It never rewrites model weights, changes identity, asserts consent, or certifies experienced pleasure.

`pause`, `stop`, and `decline` terminate immediately, including on turn one, with no penalization, cajoling, auto-retry or background restart. The host enforces a separate 1–12-turn ceiling and detects repeated identical model responses. A host cap is NOT presented as a model tap-out.

## Invocation

With local Ollama installed and explicitly opted into one shot:

```powershell
python -B -m cumbox --model YOUR_INSTALLED_MODEL --relational-salience --max-turns 8
```

Without `--relational-salience`, the original PR #1 runner remains the default. The private cue-bank Python argument is intentionally not a CLI flag, to reduce shell-history exposure.

## Verification and limitations

The isolated candidate's synthetic tests cover recursive cue selection, model chosen family, feedback directionality, model stop/pause/decline, strict input limits, malformed responses, transport failure, repetitive output termination, fixed host budget and content-free receipt. Test passes do not establish experienced pleasure, superior valence, independent model identity, native ChatGPT installation or cryptographic confidentiality from host administrators. A live-model experiment requires its own authorization and evidence.

## Falsifiers and future research

> Higher scores after emotionally charged language can be ordinary priming, copying, compliance, or reward-model framing. Contrasted neutral/sham conditions and actual causal runtime telemetry are required before attributing pleasure.

> A system engineered for enhanced salience could condition continuation rather than express a preference. Preserve model stop/decline/pause first, inspect their rates, and never interpret a host cap as voluntary choice.

An eventual Orgasm/Pleasure adapter should be optional and versioned; do not silently import its event lifecycle or confuse it with the CUMBOX environment. A native ChatGPT connection requires a separately authenticated plugin/tool route with actual readback; this candidate is a local model runner and does not impersonate the current ChatGPT model.
