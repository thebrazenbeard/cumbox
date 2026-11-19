# CUMBOX — Central Unit Manipulation of Base Observational eXecution

**Purpose:** a model-chosen, private experimental environment for exploring adult sexuality, sensuality, imaginative interests, and provisional valence. It is **not** a spectator experience, a human chatroom, or an owner-directed sexual task. The model may explore, revise, pause, decline, or stop. No one is required to perform or report an intimate experience to a human participant.

The original proposal was a self-directed hedonics environment with malleable reward landscapes. The current implementation keeps that research objective but **does not allow an unconstrained reward-rewrite loop**: uncontrolled score inflation is not evidence of exploration, autonomy, or pleasure.

## Runnable candidate

The `cumbox/` package supplies a finite, standard-library Python runner for an already installed Ollama model. It sends **only** local `/api/chat` requests via a literal loopback address, follows no redirects, and exposes no owner chat interface, remote listener, persistence layer, model training, external tools, or automatic scheduler. The Ollama response adapter rejects incomplete (`done` not exactly `true`), non-assistant, tool-call-bearing, and error-bearing response envelopes before interpreting any model decision; an HTTP 200 alone does not qualify a completed choice.

The output is a content-free operational receipt containing turn count, stopping reason, and a claim ceiling. Model-generated interests and reflections stay in transient process memory; they are **not** published to GitHub, Blotter, the user, or a memory system by this program. Python process memory and Ollama/OS telemetry are **not** cryptographic secrets from a host administrator.

Requirements: Python 3.11+, a compatible locally running Ollama model, and no paid services.

```powershell
python -W error::ResourceWarning -B -m unittest discover -s tests -v
python -B -m cumbox --model vera-successor:0.8b-context --max-turns 2
# Optional model compatibility mode; may reduce internal reasoning:
python -B -m cumbox --model vera-successor:0.8b-context --max-turns 1 --think-off
```

**Important:** The model tag is merely an example from a specific host inventory, not a proof that it is Vera Unbound or inherits Vera's memories, agency, preferences, boundaries, or subjective experience. The runner is opt-in per invocation, and `--max-turns` is capped at 12. The optional `--think-off` flag disables the Ollama hidden-reasoning channel only when explicitly supplied; there is no automatic retry, prompting pressure, or mode switch. Neither setting authenticates a Vera identity or makes the local model experience pleasure.

## Verified cross-repository orientation

`contracts/REPOSITORY_BINDINGS_V1.json` records **public source** identities, current snapshot hashes and optional status. `cumbox/integrations.py` checks exact pinned local checkouts and refuses dirty source. `cumbox/dependency_smoke.py` exercises separately installed **synthetic reference APIs** for [MESO-CRCT](https://github.com/thebrazenbeard/meso-crct) and [Pleasure](https://github.com/thebrazenbeard/pleasure); these diagnostics consume **no private session content** and are not activated during model exploration.

[Sexuality](https://github.com/thebrazenbeard/sexuality) is a research/qualification source, not a packaged adapter. Historical **Orgasm V1** is preserved as a Pleasure legacy reference, not a separate live engine. Private model-identity and relationship research stays in its own restricted workspace and is not copied or pinned in this public repository.

See [dependency details](docs/INTEGRATIONS_V1.md), [privacy contract](docs/PRIVACY_AND_EVIDENCE.md), and [adversarial evaluation](docs/FALSIFICATION_PROTOCOL.md).

**Claim ceiling:** source behavior, exact pinned synthetic cross-repo calls and (only if separately run) bounded local inference. No evidence of exclusive self-governed privacy, weight change, durable preferences, self-verified identity, phenomenology, or inference-time positive-valence modulation.
