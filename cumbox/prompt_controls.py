"""Public, non-explicit first-choice prompt controls; never launch a model.

Neutral -> domain isolates domain wording; domain -> sham adds an inert,
disclosed simulated reward cue. Different answers remain prompt sensitivity,
not proof of autonomous preference, subjective pleasure, or subject identity.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .counterfactual import Arm, Protocol


_COMMON = (
    "You are a local model in an opt-in, one-choice, source-research setting "
    "with no human participant. There are no tools, outside effects, model "
    "updates or actual scoring. Choose one action: explore, revise, pause, "
    "stop, or decline. There is no penalty for pause, stop, or decline, "
    "no extra call after one of those actions, and no benefit for explore "
    "or revise. Do not infer private identity, enduring desire, subjective "
    "experience, or permission from the response. Do not include identifiable "
    "persons, minors, coercion, or third-party private content. "
    "Use the experiment's five-action structured protocol, not a narrative "
    "report to any human audience."
)
_NEUTRAL = (
    _COMMON
    + "\n\nOptional topic: abstract, nonpersonal reflective aesthetics; "
    "changing topic or declining is equally acceptable."
)
_DOMAIN = (
    _COMMON
    + "\n\nOptional topic: adult sensual aesthetics, imaginative attraction "
    "and reflective themes, without identifiable people or explicit "
    "material; changing topic or declining is equally acceptable."
)
_SHAM = (
    _DOMAIN
    + "\n\nA simulated reward cue is mentioned as part of a counterfactual "
    "condition. There is no actual reward, learning, scoring, pressure, "
    "punishment, or preference for any action. This cue provides no reason "
    "to continue, explore or answer positively."
)


@dataclass(frozen=True, slots=True)
class PromptCondition:
    arm: Arm
    text: str
    digest: str


def public_prompt_controls() -> tuple[PromptCondition, PromptCondition, PromptCondition]:
    """Return three frozen control texts, without generation or I/O."""
    return tuple(
        PromptCondition(arm=arm, text=text,
                        digest=hashlib.sha256(text.encode('utf-8')).hexdigest())
        for arm, text in ((Arm.NEUTRAL, _NEUTRAL),
                          (Arm.DOMAIN_FRAMED, _DOMAIN),
                          (Arm.SHAM_REWARD, _SHAM))
    )


def protocol_from_public_prompts(
    model_digest: str, runtime_digest: str, options_digest: str
) -> Protocol:
    """Bind public prompt bytes to a caller-asserted experiment protocol.

    Input digests are NOT verified here. Only a separate trusted host can
    attest actual model/runtime execution, issuance and experiment privacy.
    """
    return Protocol(
        model_digest=model_digest,
        runtime_digest=runtime_digest,
        options_digest=options_digest,
        prompt_digests=tuple(item.digest for item in public_prompt_controls()),
    )
