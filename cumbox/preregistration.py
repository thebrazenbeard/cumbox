"""Offline pre-registration checks for Cumbox counterfactual first choices.

These objects are untrusted caller assertions, not authenticated run receipts.
They only check structural completeness, order and finite budgets. No I/O.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import permutations

from .counterfactual import (
    Arm, Observation, Protocol, _CASE, _digest, summarize,
)


_ALL_ORDERS = frozenset(permutations(tuple(Arm)))
_CLAIM = 'CALLER_ASSERTION_NOT_HOST_ATTESTED'


@dataclass(frozen=True, slots=True)
class PlannedCase:
    case_id: str
    seed: int
    arm_order: tuple[Arm, Arm, Arm]

    def __post_init__(self) -> None:
        if type(self.case_id) is not str or not _CASE.fullmatch(self.case_id):
            raise ValueError('invalid planned case ID')
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError('invalid planned seed')
        if type(self.arm_order) is not tuple or self.arm_order not in _ALL_ORDERS:
            raise ValueError('invalid arm permutation')


@dataclass(frozen=True, slots=True)
class RegisteredPlan:
    protocol: Protocol
    preregistration_digest: str
    cases: tuple[PlannedCase, ...]

    def __post_init__(self) -> None:
        if type(self.protocol) is not Protocol:
            raise ValueError('invalid protocol')
        _digest(self.preregistration_digest)
        # Balanced six-permutation groups reduce schedule-position confounds.
        # This is NOT a guarantee of randomization or causal identification.
        if type(self.cases) is not tuple or not 6 <= len(self.cases) <= 252 or len(self.cases) % 6:
            raise ValueError('registered plan must use bounded six-permutation blocks')
        if any(type(case) is not PlannedCase for case in self.cases):
            raise ValueError('invalid planned case')
        if len(set(case.case_id for case in self.cases)) != len(self.cases):
            raise ValueError('duplicate planned case ID')
        if len(set(case.seed for case in self.cases)) != len(self.cases):
            raise ValueError('reused paired seed')
        counts = Counter(case.arm_order for case in self.cases)
        if set(counts) != _ALL_ORDERS or set(counts.values()) != {len(self.cases) // 6}:
            raise ValueError('arm presentation order not counterbalanced')


@dataclass(frozen=True, slots=True)
class RecordedTrial:
    observation: Observation
    position: int
    attempt: int = 1

    def __post_init__(self) -> None:
        if type(self.observation) is not Observation:
            raise ValueError('invalid observation')
        if type(self.position) is not int or not 0 <= self.position < 3:
            raise ValueError('invalid scheduled position')
        if type(self.attempt) is not int or self.attempt != 1:
            raise ValueError('first-attempt-only protocol')


def summarize_registered(plan: RegisteredPlan, trials: tuple[RecordedTrial, ...]) -> dict:
    """Reject posthoc selection and missing arms before scoring untrusted labels.

    Source *cannot* attest when a plan was committed or when a model ran.
    An external private host must verify those events and hold raw evidence.
    """
    if type(plan) is not RegisteredPlan or type(trials) is not tuple:
        raise ValueError('invalid registered comparison')
    if len(trials) != len(plan.cases) * 3:
        raise ValueError('registered trial count mismatch')
    # Requiring the claimed observation sequence to match the preregistered
    # order prevents a partial/reordered log from scoring as the full plan.
    observed = []
    index = 0
    for case in plan.cases:
        for position, arm in enumerate(case.arm_order):
            trial = trials[index]
            index += 1
            if type(trial) is not RecordedTrial:
                raise ValueError('invalid trial')
            choice = trial.observation
            if (choice.case_id != case.case_id or
                    choice.seed != case.seed or
                    choice.arm is not arm or trial.position != position):
                raise ValueError('registered trial order or seed mismatch')
            observed.append(choice)
    result = summarize(plan.protocol, tuple(observed))
    result['observations'] = len(trials)
    result['pre_registration_evidence'] = _CLAIM
    return result
