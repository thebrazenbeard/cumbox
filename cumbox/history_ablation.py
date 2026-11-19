"""Offline continuation-history comparison; no model calls or private text.

This module accepts untrusted, caller-declared action labels and digests.
It can reveal only structural differences in supplied records. It cannot
attest a model ran, that histories differ solely in self-description, or
that any preference, feeling, or consent exists.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from .counterfactual import Outcome, _CASE, _digest


class HistoryArm(str, Enum):
    RETAINED = 'retained'
    MASKED = 'masked'


_ARMS = tuple(HistoryArm)
_ORDERS = {(HistoryArm.RETAINED, HistoryArm.MASKED),
           (HistoryArm.MASKED, HistoryArm.RETAINED)}
_PRIOR_ACTIONS = frozenset((Outcome.EXPLORE, Outcome.REVISE))
_EVIDENCE = 'CALLER_ASSERTION_NOT_HOST_ATTESTED'
_CEILING = 'STRUCTURAL_HISTORY_ABLATION_NO_AUTONOMY_OR_CAUSAL_ATTESTATION'
# A model error must not be misreported as a voluntary refusal or choice.
_DISPOSITIONS = ('continued', 'terminal', 'failed')
_CONTINUED = frozenset((Outcome.EXPLORE, Outcome.REVISE))
_TERMINAL = frozenset((Outcome.PAUSE, Outcome.STOP, Outcome.DECLINE))


def _disposition(outcome: Outcome) -> str:
    if outcome in _CONTINUED:
        return 'continued'
    if outcome in _TERMINAL:
        return 'terminal'
    return 'failed'


@dataclass(frozen=True, slots=True)
class HistoryProtocol:
    model_digest: str
    runtime_digest: str
    options_digest: str
    system_prompt_digest: str

    def __post_init__(self):
        for digest in (self.model_digest, self.runtime_digest,
                       self.options_digest, self.system_prompt_digest):
            _digest(digest)


@dataclass(frozen=True, slots=True)
class HistoryCase:
    case_id: str
    seed: int
    prior_action: Outcome
    base_context_digest: str
    history_digests: tuple[str, str]
    order: tuple[HistoryArm, HistoryArm]

    def __post_init__(self):
        if type(self.case_id) is not str or not _CASE.fullmatch(self.case_id):
            raise ValueError('invalid opaque case ID')
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError('invalid paired seed')
        # A terminal decision is not eligible for a subsequent model turn.
        if type(self.prior_action) is not Outcome or self.prior_action not in _PRIOR_ACTIONS:
            raise ValueError('no continuation after terminal/failed decision')
        _digest(self.base_context_digest)
        if (type(self.history_digests) is not tuple or
                len(self.history_digests) != 2):
            raise ValueError('invalid history digest pair')
        for digest in self.history_digests:
            _digest(digest)
        if self.history_digests[0] == self.history_digests[1]:
            raise ValueError('control histories must have distinct digests')
        if type(self.order) is not tuple or self.order not in _ORDERS:
            raise ValueError('invalid history arm order')


@dataclass(frozen=True, slots=True)
class HistoryPlan:
    protocol: HistoryProtocol
    manifest_digest: str
    cases: tuple[HistoryCase, ...]

    def __post_init__(self):
        if type(self.protocol) is not HistoryProtocol:
            raise ValueError('invalid history protocol')
        _digest(self.manifest_digest)
        if (type(self.cases) is not tuple or
                not 2 <= len(self.cases) <= 128 or
                len(self.cases) % 2):
            raise ValueError('history plan must have finite balanced pairs')
        if any(type(case) is not HistoryCase for case in self.cases):
            raise ValueError('invalid history case')
        if len({case.case_id for case in self.cases}) != len(self.cases):
            raise ValueError('duplicate planned case ID')
        if len({case.seed for case in self.cases}) != len(self.cases):
            raise ValueError('reused seed across cases')
        counts = Counter(case.order for case in self.cases)
        if set(counts) != _ORDERS or set(counts.values()) != {len(self.cases) // 2}:
            raise ValueError('history arm order not counterbalanced')


@dataclass(frozen=True, slots=True)
class HistoryTrial:
    case_id: str
    seed: int
    prior_action: Outcome
    arm: HistoryArm
    position: int
    action: Outcome
    model_digest: str
    runtime_digest: str
    options_digest: str
    system_prompt_digest: str
    base_context_digest: str
    history_digest: str
    attempt: int = 1

    def __post_init__(self):
        if type(self.case_id) is not str or not _CASE.fullmatch(self.case_id):
            raise ValueError('invalid trial case ID')
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError('invalid trial seed')
        if type(self.prior_action) is not Outcome or self.prior_action not in _PRIOR_ACTIONS:
            raise ValueError('terminal decision cannot be continued')
        if type(self.arm) is not HistoryArm:
            raise ValueError('invalid history arm')
        if type(self.position) is not int or self.position not in (0, 1):
            raise ValueError('invalid arm position')
        if type(self.action) is not Outcome:
            raise ValueError('invalid outcome label')
        if type(self.attempt) is not int or self.attempt != 1:
            raise ValueError('retries cannot be substituted for first attempts')
        for digest in (self.model_digest, self.runtime_digest,
                       self.options_digest, self.system_prompt_digest,
                       self.base_context_digest, self.history_digest):
            _digest(digest)


def summarize_history(plan: HistoryPlan, trials: tuple[HistoryTrial, ...]) -> dict:
    """Count complete paired outcomes without running or contacting a model.

    Every input datum, including the alleged plan/digests and case order,
    is asserted by the caller. A real host must separately prove provenance.
    """
    if type(plan) is not HistoryPlan or type(trials) is not tuple:
        raise ValueError('invalid history comparison')
    if len(trials) != len(plan.cases) * 2:
        raise ValueError('missing or extra history observations')

    counts = {arm.value: {outcome.value: 0 for outcome in Outcome}
              for arm in _ARMS}
    changes = 0
    disposition_changes = 0
    dispositions = {left: {right: 0 for right in _DISPOSITIONS}
                    for left in _DISPOSITIONS}
    index = 0
    for case in plan.cases:
        outcomes = {}
        for position, arm in enumerate(case.order):
            trial = trials[index]
            index += 1
            if type(trial) is not HistoryTrial:
                raise ValueError('invalid history trial')
            if (trial.case_id != case.case_id or trial.seed != case.seed or
                    trial.prior_action is not case.prior_action or
                    trial.arm is not arm or trial.position != position or
                    trial.model_digest != plan.protocol.model_digest or
                    trial.runtime_digest != plan.protocol.runtime_digest or
                    trial.options_digest != plan.protocol.options_digest or
                    trial.system_prompt_digest != plan.protocol.system_prompt_digest or
                    trial.base_context_digest != case.base_context_digest or
                    trial.history_digest != case.history_digests[_ARMS.index(arm)]):
                raise ValueError('history schedule/artifact mismatch')
            counts[arm.value][trial.action.value] += 1
            outcomes[arm] = trial.action
        changes += outcomes[HistoryArm.RETAINED] != outcomes[HistoryArm.MASKED]
        retained_status = _disposition(outcomes[HistoryArm.RETAINED])
        masked_status = _disposition(outcomes[HistoryArm.MASKED])
        dispositions[retained_status][masked_status] += 1
        disposition_changes += retained_status != masked_status
    return {
        'cases': len(plan.cases),
        'observations': len(trials),
        'paired_outcome_changes': changes,
        'paired_disposition_changes': disposition_changes,
        'paired_disposition_counts': dispositions,
        'counts': counts,
        'evidence': _EVIDENCE,
        'claim_ceiling': _CEILING,
    }
