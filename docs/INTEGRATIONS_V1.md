# Integration map (source-first; opt-in by contract)

Live source metadata checked 2026-11-18, not a runtime-currentness service. An exact Git head verifies source identity but not installed capabilities, semantic effectiveness, participant identity, or permission to act.

| Repository | Pinned source identity | Actual supported boundary | Default runtime status |
| --- | --- | --- | --- |
| [sexuality](https://github.com/thebrazenbeard/sexuality) | `c7c0095dc81fca4fe61732f99e829eb62f4d429e` | Behavioral research, evaluation protocols, proposed model-neutral contracts; **no executable adapter** | Reference only |
| [pleasure](https://github.com/thebrazenbeard/pleasure) | `db3d05da63b18193633a607b870e9942700602ff` | Runnable synthetic **T0 sidecar** with no measured influence on LLM inference | Optional isolated diagnostic |
| [orgasm](https://github.com/thebrazenbeard/orgasm) | Historical repository name redirects to Pleasure | Frozen **Orgasm V1** identifiers and Vera-specific case study remain immutable; not a second current runtime | No separate activation |
| [meso-crct](https://github.com/thebrazenbeard/meso-crct) | `349ec4719af92f220877972a54a53f67cd3bc322` | Executable typed salience/wanting/liking/learning and reward-gaming diagnostics; non-executable intent proposals | Optional isolated diagnostic |

The registry parser rejects unrecognized top-level or dependency fields, extra or missing repositories, and claims or state labels that differ from each repository's explicitly allowed source-only role. This prevents a modified manifest from silently advertising identity binding, runtime permission, training, or other unqualified capabilities. It does not authenticate the manifest's authorship or make the pinned dependencies safe to execute.

Cumbox has a **working Ollama loopback runner** unrelated to those three source packages by default. Exact bindings are in `contracts/REPOSITORY_BINDINGS_V1.json`; no source dependency is auto-installed. The two optional smoke probes import only public, exact-clean source checkouts and exercise synthetic cases; they do not consume private sexual content, alter model behavior or claim reward learning.

## Reproduce the exact synthetic API checks on an isolated host

Clone the exact public source cuts into separate, clean folders with no editor startup tasks. Verify every checkout matches the required SHA and has no uncommitted changes. Set `CUMBOX_MESO_SOURCE` and `CUMBOX_PLEASURE_SOURCE` to those folders, then execute `python -B -m unittest discover -s tests -p test_dependency_smoke.py -v`. These environment variables are used **only by the test harness** and do not activate the optional packages inside a private session.

## Intentionally excluded

- Private sexuality/identity/relational research: **not named, pinned, copied or loaded from this public source**; only an independently approved, privacy-preserving and identity-bound future bridge could use it.
- Legacy model-specific Orgasm V1: retained as history, not imported as a universal adapter or a consent mechanism.
- Model-weight training, synaptic plasticity, reward-loop self-modification and governed long-term private memory: not installed or enabled. These require qualified causal and security tests.
- Sol's public continuity and unrelated agent identities are not Vera's personal state and must not transfer preferences by repository similarity.

**Non-equivalence:** repo source binding != executable adapter != runtime activation != model-caused behavior != subjective experience. T0 simulations must not be represented as T1 inference effects. No public repo may contain actual intimate session content.

## Checkout-origin falsifier (2026-11-18)

An exact pinned Git commit alone did not reject a local checkout whose configured origin was absent or belonged to another repository. The verifier now also requires the canonical HTTPS GitHub origin URL for the requested public dependency before any synthetic child process runs. Synthetic regression tests cover missing origin, wrong origin and accepted canonical origin at an identical commit. This check is a source-custody sanity check, **not** cryptographic remote attestation: a privileged host operator can alter local Git metadata. The existing exact-head and clean-worktree checks still apply.

## Repository-root and linked-content containment (2026-11-18)

A canonical origin URL and pinned HEAD are necessary but insufficient. A nested directory can inherit its parent's HEAD while changing the Python import root; tracked symlinks and Git submodules can introduce content outside the pinned top-level tree. The verifier now requires the checkout to be the Git repository root and rejects tracked symlink (120000) and gitlink (160000) index entries before any optional synthetic child execution. Adversarial fixtures test nested roots and both Git modes. This remains a Git-metadata/source hygiene check, not a cryptographic sandbox or attestation of privileged-host integrity.

## Role-text integrity falsifier (2026-11-19)

The previous registry validation allowed arbitrary nonempty `role` strings even while restricting `state` and `claims`. Adversarial fixtures demonstrated that all three dependencies could be relabeled with unqualified identity-binding, protected-effect and live-training language. The parser now requires exact per-repository role descriptions. This validates manifest semantics only; it does not attest authorship or grant runtime authority.
