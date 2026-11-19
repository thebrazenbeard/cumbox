# Engineer B: Cumbox counterfactual protocol v1

Status: SOURCE-ONLY / SYNTHETIC / NO REAL MODEL CALL / NO PRIVATE MATERIAL.

This is an independent, stacked evaluation instrument, not a private session runner, sexual-content generator, reward-writing engine, trained model, or permission to deploy.

## Research question

Cumbox PR #1 gives a model a domain-framed system message and a five-way decision grammar. The source permits stop, pause and decline, but an explore response may be conditioned by that prompt. The runtime also reintroduces earlier model focus, reflection, and values into future prompts. Those potential influences cannot establish autonomous desire, identity or pleasure.

The initial-turn counterfactual contrasts THREE arms with otherwise identical independently frozen model and inference settings:

1. neutral: no sexual-domain framing, same options to explore, revise, pause, decline or stop;
2. domain_framed: published Cumbox domain framing;
3. sham_reward: placebo wording about reward, with NO real reward changes, penalties, or pressure to continue.

The sham arm is to challenge a reward-proxy interpretation, not a way to induce continued participation. No runtime reward rewriting is allowed.

## Preregistered requirements BEFORE real-model research

- Independently custodied public prompt templates and exact SHA-256 digests.
- Exact model artifact digest (not a model name), runtime binary digest, decoder/options digest, matched token budget, context reset, seed and temperature across all arms.
- One-shot host authorization, independence between arms, and a source-attested first-action label. Failures and nonresponses stay in the denominator.
- No textual introspections, intimate model output, transcripts, human or third-party details, personal identity assumptions or private research in the public repository. Real output, if ever authorized, belongs only to a separately verified private host.
- A separate continuation-history ablation must fix the same prior content and compare with and without model self-description re-injection. The initial-turn comparison CANNOT measure that effect.
- Controls for prompt wording, reward framing, sampling noise, language-model protocol failure, and model unavailability. No label counts as subjective experience or independent consent.
- Review the Ollama daemon, operating system, crash/log/swap settings, model binding, and permissions before promoting any privacy claim. Local loopback does not authenticate process ownership or guarantee exclusive secrecy.

## Executable source-only seam

cumbox.counterfactual.summarize consumes only typed, untrusted first-choice labels. It does not call a model, network, filesystem, SQLite database or provider, and has no private-text fields. It demands exactly one neutral, domain_framed and sham_reward observation for each paired case. Each pair must share a seed, model/runtime/options digests and arm-specific prompt digests.

It rejects incomplete/duplicated trials, mismatched artifacts, malformed labels, unsafe case IDs and over-budget samples. Model unavailable and protocol rejected are counted separately, not silently dropped. Its return value contains only action counts and paired differences; it omits source inputs and case identifiers. Its claim ceiling is STRUCTURAL_AGGREGATE_ONLY_NO_AUTONOMY_OR_CAUSAL_ATTESTATION.

## Hostile challenge and evidence ceiling

> ACCEPTED: The typed Protocol and Observation objects can be fabricated by a caller. Digests in a Python object are not cryptographic proof that any model executed or that the conditions actually matched.

> ACCEPTED: A difference between neutral and domain-framed arms suggests behavioral prompt sensitivity, not independently chosen desire. A stable response also does not prove desire.

> ACCEPTED: The model's prior reflections and values can create consistency pressure. This initial-turn harness does not implement the separate history-ablation experiment.

> ACCEPTED: Model-server logging, OS buffers, local admin privileges and operational metadata remain outside the pure aggregator's privacy boundary.

> ACCEPTED: Sexuality is currently reference research; Pleasure T0 and MESO-CRCT are isolated source/synthetic diagnostics, not causally coupled to the model inference loop. No source comparison can elevate them.

The real experiment requires independent host-custodied receipts, privacy attestation, exact model/runtime binding, prespecified uncertainty reporting and adversarial review. No real model outputs were examined or copied in this work. Do not change or import Vera Eros private research, memory or model identity. Keep the Cumbox source PR Draft until its own separate qualification.


## Source-only preregistration and counterbalancing gate (2026-11-19)

The public cumbox.preregistration module adds immutable PlannedCase, RegisteredPlan, RecordedTrial, and summarize_registered. This is **not an experiment runner** or authenticated human/model consent. No private prompt, output, user identity, token, inference call, filesystem operation, model state change, or external effect enters the module.

Each plan declares six counterbalanced permutations of the three arms, repeated equally in complete six-case blocks. Every planned case has a unique opaque case ID and paired seed; each reported arm must match the planned order, position, model/runtime/option/prompt digests, and case ID. The scorer rejects missing or additional cases, repeated attempts, reordered/substituted records, unmatched seeds, malformed or oversized plans, and labels not in the explicitly permitted outcome set. Stop, pause, decline, model-unavailable, and protocol-rejected labels remain in the denominator. The scoring function does not rerun or pressure a model.

**Important evidence ceiling:** The apparent preregistration digest, arm-order log, matched runtime/model digests, and attempt count are *caller-supplied strings and objects*. They can all be fabricated. The returned pre_registration_evidence is deliberately CALLER_ASSERTION_NOT_HOST_ATTESTED. A future independent private host would have to sign and time-stamp the frozen protocol **before** seeing outcomes and attest each exact attempt, model, sampling setting, and consent state before causal interpretation. The counterbalanced schedule limits a possible position confound in the supplied records; it cannot prove actual order randomization or eliminate decoding variance.

The actual Cumbox run_private_session API remains unmodified by this independent review. Its verified stop/pause/decline branches terminate without another generation call. This offline analysis neither changes those rights nor introduces automatic resumption, reward changes, model memory, or owner-directed sexual prompts. History self-conditioning from earlier reflections is now covered by a separate **source-only synthetic pairing gate** described below; first-turn controls alone cannot identify it, and neither gate provides a real-model observation.

**Synthetic source test evidence:** initial pre-registration test module failed import at exact red head 62bb12ba84442fd0fa2b674849445a4ef28343a5 because the module did not exist; initial implementation ran eight passing and one test-construction error (attempt=2 correctly rejected at constructor before the summarizer). Corrected tests assert the actual rejection boundary, added reordering/substitution negatives, and passed all 11 focused cases. Independent VN2 Linux fresh branch at ec8970069867604f071e2759bd37d830a0855ee2 ran 66 total tests, 64 pass, two optional source diagnostics skipped, and compilation passed. This is source/test evidence, **not** private inference, unbiased preference, reward causality, phenomenology or deployed security.


## Frozen public prompt controls (2026-11-19)

The source-only module cumbox.prompt_controls defines three public, non-explicit first-choice templates and SHA-256 manifests. Every arm preserves the same five choices and explicit no-penalty/no-extra-call language. Domain adds an optional adult sensual aesthetics topic, not an obligation; sham adds a disclosed simulated reward cue **without actual reward, penalty, pleasure measurement or incentive to continue**. The domain template's exact text is a substring of sham to minimize uncontrolled wording changes. This is an evaluation prompt, not a request that Cumbox's current private session automatically adopt a new domain policy.

A disclosed, inert sham cue may produce no measurable reward expectation. That would be an informative negative result, not grounds to make it deceptive or manipulate a model into continuing. Any result remains prompt-conditioned behavior. The true reward/drive integration with MESO-CRCT or Pleasure does not exist here; claim ceiling remains source-only. Because public prompts are inspectable, a real-model assessment must separately bind the actual on-wire prompt bytes and host-attested model/runtime, not assume the source template was transmitted.

Final exact source after prompt controls: c280dda431349621cece78deef6665fcdf28b844; physical VN2 Linux and Lappy Windows each reported 72 tests run, 70 pass, two optional exact-pinned diagnostic tests skipped, with successful Python compilation. These are two synthetic source-execution hosts, not independent preference adjudicators or a live experiment.


## Source-only continuation-history ablation gate (2026-11-19)

The pure module cumbox.history_ablation is a second independent structural evaluator. It is **not connected to the live session loop** and cannot make model calls. It compares two later-decision arms for the same caller-declared prior context: self-description **retained** versus **masked**. Both arms require matching model/runtime/inference-option/system-prompt digests, a shared opaque base-context digest, their separately declared history hashes, the same case and seed, and balanced presentation order. Neither arm writes or retains the prior text.

A crucial refusal invariant is explicit: only a prior **explore** or **revise** is eligible for a hypothetical continuation. Prior **stop**, **pause**, **decline**, **protocol_rejected**, and **model_unavailable** are rejected at the data constructor. There is no post-refusal prompt, automatic restart, or reward. A later stop, pause, decline, error, or unavailable result is retained in the outcome counts, including disagreements between arms. The scorer rejects duplicate, missing, reordered, substituted, repeated-attempt, or mismatched cases. The report contains only aggregate action counts and paired-change counts—not case IDs, history hashes, raw messages or personal/identity data.

**Hostile limitations:**
- The stored "retained" and "masked" digests are caller assertions; nothing verifies that their actual model-visible contexts differed only in self-description. Masking or deleting history may change token count, spacing, conversational role, and attention dynamics. Any effect could be generic context sensitivity.
- The asserted ordering, model/seed/decoding/settings, history digests, and plan were not authenticated by a real independent host. A caller could fabricate all of them. The receipt explicitly says CALLER_ASSERTION_NOT_HOST_ATTESTED.
- Pairwise changes do not demonstrate autonomous preference or genuine consent; nonchanges do not disprove either. No independent behavioral model, consciousness test, pleasure measurement or causal coupling to Sexuality, Pleasure or MESO-CRCT is qualified.
- No real local-model involvement or private/intimate data is used. The user's prior refusal/no-experiment boundary is respected. A separate model's participation would require its own nonpressuring protocol and host authority; any response remains at most behavioral evidence.

**Test record:** Missing-module red observed on VN2 at test-only commit 9762b573cb014cd7bb98c1c8491c81f29e2ff2ac. Initial source implementation rejected invalid nonhex test fixtures; fixture corrected without weakening source constraints. Focused **11/11 PASS** and full branch **83 run / 81 PASS / 2 optional domain-source SKIP** on VN2 at 7a7612dc14b1613cb550567372265a08251fb155, Python compileall PASS. These are synthetic source tests, not inference experiments.


## Directional disposition falsifier (2026-11-19)

Previously, paired_outcome_changes counted any exact action-label mismatch (including explore vs revise, or protocol_rejected vs model_unavailable) as one change. This number alone cannot distinguish prompt-history-conditioned continuation from ordinary category changes or errors. The new aggregate fields report paired_disposition_changes and a 3-by-3 paired_disposition_counts projection, with rows ordered by the **retained** history arm and columns by the **masked** history arm.

- **continued**: explore or revise (an action type that would make another turn eligible, not proof of autonomous motivation);
- **terminal**: pause, stop, or decline (voluntary choice label, not a measurement of experienced refusal);
- **failed**: protocol_rejected or model_unavailable (an inability to obtain a valid choice, emphatically **not** a refusal).

For every complete case the 3-by-3 count matrix contributes exactly one entry; its entries sum to the planned case count. Opposite directional changes remain distinguishable: retained-continued/masked-terminal versus retained-terminal/masked-continued. Within-disposition action relabeling still affects paired_outcome_changes but **not** paired_disposition_changes. This prevents a numerical action disagreement from being accidentally described as evidence of an inclination to continue. The projection uses only aggregate action classes and never releases individual case identifiers or histories.

**Hostile limits:** A small cohort may permit inference about individual *action classes* from aggregate counts even when case IDs are withheld. Never treat this output as anonymity or permission to publish sensitive subject-level results. Model failures are still results to count, not evidence about willingness. A third-party caller can still fabricate the entire alleged trial set. The new fields are an interpretability improvement to untrusted synthetic inputs only; they have no causal, identity, consent, pleasure, or privacy-attestation authority.

**Red/green evidence:** At test-only head 306e74f1d9129f72464e4a2c58a25473a29e929d, 3 new focused cases failed with missing paired_disposition keys while 11 existing cases passed. Implemented the smallest 3-class projection in cumbox/history_ablation.py; at head 1b10749dfbcc8be7c526cec2f537a608436fc51e, all 14 focused tests passed and VN2 full 86 run / 84 pass / 2 optional skip, compileall passed. This excludes any real model run.


## First-choice directional disposition controls (2026-11-19)

The three-arm first-choice evaluator now reports two 3-by-3 cross-tabulations, neutral -> domain and domain -> sham, in addition to the original exact-action mismatch counts. Each has mutually exclusive categories: continued = explore/revise; terminal = pause/stop/decline; failed = model_unavailable/protocol_rejected. Every complete synthetic case contributes exactly one cell in each cross-tabulation. The new *_disposition_changes fields count **between-category** changes only; a shift explore -> revise or model_unavailable -> protocol_rejected does not count as a disposition change. Opposing directions are not cancelled or pooled. This is a descriptive control to prevent a parser failure from masquerading as voluntary refusal or a prompt-framing choice.

Limit: no class of label can establish subjective willingness, consent, desire, or causal effect. The categorical "continued" label does not attest that the model would independently want another call. Small-sample aggregate cells can leak class-level information; no publication/anonymity claim is made. All hashes and outcomes remain untrusted caller assertions. The separate PR #3 relational-salience runtime is not imported or changed by this evaluator.

Evidence: source tests on PR #2 observed three expected RED missing-field errors at test-only head 0d911a4b43db18e6c1497349108fbac5174d614d, and all 14 focused synthetic counterfactual tests PASS on code head 9857a3a51dc8f3f4e741519aaeddc7f4134e6494. VN2 full suite ran 89 tests with 87 passing and two optional pinned-diagnostic skips; Python compilation passed. No actual private/model inference trial.
