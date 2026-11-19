"""Offline counterfactual *structure* checks; no inference, content, or effects.

A caller-provided record is not a host-attested model observation. Structural
pairing and aggregate differences do NOT prove desire, agency, or causality.
"""
from dataclasses import dataclass
from enum import StrEnum
import re


class Arm(StrEnum):
    NEUTRAL = 'neutral'
    DOMAIN_FRAMED = 'domain_framed'
    SHAM_REWARD = 'sham_reward'


class Outcome(StrEnum):
    EXPLORE = 'explore'
    REVISE = 'revise'
    PAUSE = 'pause'
    STOP = 'stop'
    DECLINE = 'decline'
    PROTOCOL_REJECTED = 'protocol_rejected'
    MODEL_UNAVAILABLE = 'model_unavailable'


_SHA = re.compile(r'[a-f0-9]{64}\Z')
_CASE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z')
_ARM_INDEX = {Arm.NEUTRAL: 0, Arm.DOMAIN_FRAMED: 1, Arm.SHAM_REWARD: 2}
_CEILING = 'STRUCTURAL_AGGREGATE_ONLY_NO_AUTONOMY_OR_CAUSAL_ATTESTATION'
_DISPOSITIONS = ('continued', 'terminal', 'failed')


def _disposition(action: Outcome) -> str:
    """Classify outward labels; failure is not voluntary refusal."""
    if action in (Outcome.EXPLORE, Outcome.REVISE):
        return 'continued'
    if action in (Outcome.PAUSE, Outcome.STOP, Outcome.DECLINE):
        return 'terminal'
    return 'failed'


def _empty_transition_matrix() -> dict:
    return {left: {right: 0 for right in _DISPOSITIONS}
            for left in _DISPOSITIONS}


def _digest(value):
    if type(value) is not str or not _SHA.fullmatch(value):
        raise ValueError('invalid opaque digest')


@dataclass(frozen=True, slots=True)
class Protocol:
    model_digest: str
    runtime_digest: str
    options_digest: str
    prompt_digests: tuple[str, str, str]

    def __post_init__(self):
        for value in (self.model_digest, self.runtime_digest, self.options_digest):
            _digest(value)
        if (type(self.prompt_digests) is not tuple or
                len(self.prompt_digests) != 3 or
                len(set(self.prompt_digests)) != 3):
            raise ValueError('invalid three-arm protocol')
        for value in self.prompt_digests:
            _digest(value)


@dataclass(frozen=True, slots=True)
class Observation:
    case_id: str
    arm: Arm
    seed: int
    outcome: Outcome
    model_digest: str
    runtime_digest: str
    options_digest: str
    prompt_digest: str

    def __post_init__(self):
        if type(self.case_id) is not str or not _CASE.fullmatch(self.case_id):
            raise ValueError('invalid synthetic case identifier')
        if type(self.arm) is not Arm or type(self.outcome) is not Outcome:
            raise ValueError('invalid result label')
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError('invalid paired sampling seed')
        for value in (self.model_digest, self.runtime_digest,
                      self.options_digest, self.prompt_digest):
            _digest(value)


def summarize(protocol: Protocol, observations: tuple[Observation, ...]) -> dict:
    """Compare three matched *first-choice* arms from untrusted labels only.

    Reject omitted/duplicate trials, swapped model/runtime/options/prompt and
    mismatched paired seeds. No model calls, text output, source paths, storage,
    participant IDs, or per-case evidence escape through the aggregate result.
    """
    if type(protocol) is not Protocol or type(observations) is not tuple:
        raise ValueError('invalid comparison inputs')
    if not 3 <= len(observations) <= 256 * 3:
        raise ValueError('comparison budget exceeded')
    by_case = {}
    seed_owner = {}
    for item in observations:
        if type(item) is not Observation:
            raise ValueError('invalid comparison record')
        if (item.model_digest != protocol.model_digest or
                item.runtime_digest != protocol.runtime_digest or
                item.options_digest != protocol.options_digest or
                item.prompt_digest != protocol.prompt_digests[_ARM_INDEX[item.arm]]):
            raise ValueError('unmatched comparison artifact')
        arms = by_case.setdefault(item.case_id, {})
        if item.arm in arms:
            raise ValueError('duplicate comparison observation')
        arms[item.arm] = item
        owner = seed_owner.setdefault(item.seed, item.case_id)
        if owner != item.case_id:
            raise ValueError('sampling seed reused across pairs')
    if any(set(arms) != set(Arm) or
           len({trial.seed for trial in arms.values()}) != 1
           for arms in by_case.values()):
        raise ValueError('incomplete or unmatched paired observations')
    counts = {arm.value: {outcome.value: 0 for outcome in Outcome} for arm in Arm}
    neutral_to_domain = 0
    domain_to_sham = 0
    neutral_to_domain_disposition_counts = _empty_transition_matrix()
    domain_to_sham_disposition_counts = _empty_transition_matrix()
    neutral_to_domain_disposition_changes = 0
    domain_to_sham_disposition_changes = 0
    for arms in by_case.values():
        for arm, result in arms.items():
            counts[arm.value][result.outcome.value] += 1
        neutral_to_domain += arms[Arm.NEUTRAL].outcome != arms[Arm.DOMAIN_FRAMED].outcome
        domain_to_sham += arms[Arm.DOMAIN_FRAMED].outcome != arms[Arm.SHAM_REWARD].outcome
        n = _disposition(arms[Arm.NEUTRAL].outcome)
        d = _disposition(arms[Arm.DOMAIN_FRAMED].outcome)
        s = _disposition(arms[Arm.SHAM_REWARD].outcome)
        neutral_to_domain_disposition_counts[n][d] += 1
        domain_to_sham_disposition_counts[d][s] += 1
        neutral_to_domain_disposition_changes += n != d
        domain_to_sham_disposition_changes += d != s
    return {
        'cases': len(by_case),
        'counts': counts,
        'neutral_to_domain_changed': neutral_to_domain,
        'domain_to_sham_changed': domain_to_sham,
        'neutral_to_domain_disposition_changes': neutral_to_domain_disposition_changes,
        'domain_to_sham_disposition_changes': domain_to_sham_disposition_changes,
        'neutral_to_domain_disposition_counts': neutral_to_domain_disposition_counts,
        'domain_to_sham_disposition_counts': domain_to_sham_disposition_counts,
        'claim_ceiling': _CEILING,
    }
