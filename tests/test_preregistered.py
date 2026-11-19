"""Pre-registration negatives use synthetic opaque IDs and action classes only."""
import dataclasses
import itertools
import socket
import unittest
from unittest.mock import patch

from cumbox.counterfactual import Arm, Outcome, Observation, Protocol
from cumbox.preregistration import (
    PlannedCase, RegisteredPlan, RecordedTrial, summarize_registered,
)

DIGESTS = ('a'*64,'b'*64,'c'*64,('d'*64,'e'*64,'f'*64))
ORDERS = tuple(itertools.permutations(tuple(Arm)))
ACTION = (Outcome.STOP,Outcome.PAUSE,Outcome.DECLINE,
          Outcome.EXPLORE,Outcome.REVISE,Outcome.PROTOCOL_REJECTED)
P = Protocol(*DIGESTS)


def make_plan():
    return RegisteredPlan(
        protocol=P,
        preregistration_digest='9'*64,
        cases=tuple(PlannedCase(f'synthetic-{i}', i+800, order)
                    for i,order in enumerate(ORDERS)),
    )


def make_records(plan, *, replace_outcomes=None):
    records = []
    for i,case in enumerate(plan.cases):
        for position,arm in enumerate(case.arm_order):
            outcome = (replace_outcomes or {}).get((case.case_id,arm),ACTION[i])
            observed = Observation(
                case_id=case.case_id,arm=arm,seed=case.seed,outcome=outcome,
                model_digest=P.model_digest,runtime_digest=P.runtime_digest,
                options_digest=P.options_digest,
                prompt_digest=P.prompt_digests[tuple(Arm).index(arm)],
            )
            records.append(RecordedTrial(observation=observed,position=position,
                                         attempt=1))
    return tuple(records)


class RegisteredCounterfactualTests(unittest.TestCase):
    def test_six_order_balanced_cases_score_without_preference_claim(self):
        plan=make_plan()
        report=summarize_registered(plan,make_records(plan))
        self.assertEqual(report['cases'],6)
        self.assertEqual(report['observations'],18)
        self.assertEqual(report['counts']['neutral']['stop'],1)
        self.assertEqual(report['counts']['neutral']['pause'],1)
        self.assertEqual(report['counts']['neutral']['decline'],1)
        self.assertEqual(report['counts']['domain_framed']['protocol_rejected'],1)
        self.assertEqual(report['claim_ceiling'],
                         'STRUCTURAL_AGGREGATE_ONLY_NO_AUTONOMY_OR_CAUSAL_ATTESTATION')
        self.assertEqual(report['pre_registration_evidence'],'CALLER_ASSERTION_NOT_HOST_ATTESTED')
        self.assertNotIn('synthetic-',str(report))
        self.assertNotIn('99999999',str(report))

    def test_incomplete_selected_or_extra_outcome_rejected(self):
        plan=make_plan()
        rows=make_records(plan)
        for change in (rows[:-1],rows+(rows[0],)):
            with self.subTest(n=len(change)),self.assertRaises(ValueError):
                summarize_registered(plan,change)

    def test_posthoc_order_swap_rejected(self):
        plan=make_plan()
        rows=list(make_records(plan))
        rows[0]=dataclasses.replace(rows[0],position=2)
        with self.assertRaises(ValueError):
            summarize_registered(plan,tuple(rows))

    def test_repeat_attempt_is_not_accepted_as_choice(self):
        plan=make_plan()
        rows=make_records(plan)
        # Invalid attempts fail at the immutable trial constructor boundary.
        with self.assertRaises(ValueError):
            dataclasses.replace(rows[1],attempt=2)

    def test_reordering_submitted_records_is_not_a_valid_schedule(self):
        plan=make_plan()
        rows=list(make_records(plan))
        rows[0],rows[1]=rows[1],rows[0]
        with self.assertRaises(ValueError):
            summarize_registered(plan,tuple(rows))

    def test_unregistered_source_substitution_is_rejected(self):
        plan=make_plan()
        rows=list(make_records(plan))
        altered=dataclasses.replace(rows[0].observation,case_id='synthetic-impostor')
        rows[0]=dataclasses.replace(rows[0],observation=altered)
        with self.assertRaises(ValueError):
            summarize_registered(plan,tuple(rows))

    def test_wrong_or_reused_seed_rejected(self):
        plan=make_plan()
        rows=list(make_records(plan))
        rows[2]=dataclasses.replace(rows[2],observation=dataclasses.replace(
            rows[2].observation,seed=801))
        with self.assertRaises(ValueError):
            summarize_registered(plan,tuple(rows))
        with self.assertRaises(ValueError):
            RegisteredPlan(protocol=P,preregistration_digest='9'*64,
                           cases=tuple(dataclasses.replace(c,seed=800) for c in plan.cases))

    def test_plan_must_use_every_permutation_equally(self):
        plan=make_plan()
        altered=tuple(dataclasses.replace(c,arm_order=ORDERS[0]) for c in plan.cases)
        with self.assertRaises(ValueError):
            RegisteredPlan(protocol=P,preregistration_digest='9'*64,cases=altered)
        with self.assertRaises(ValueError):
            RegisteredPlan(protocol=P,preregistration_digest='9'*64,cases=plan.cases[:5])

    def test_unavailable_and_protocol_rejected_are_not_deleted(self):
        plan=make_plan()
        first=plan.cases[0]
        rows=make_records(plan,replace_outcomes={
            (first.case_id,Arm.NEUTRAL):Outcome.MODEL_UNAVAILABLE,
            (first.case_id,Arm.SHAM_REWARD):Outcome.PROTOCOL_REJECTED,
        })
        result=summarize_registered(plan,rows)
        self.assertEqual(result['counts']['neutral']['model_unavailable'],1)
        self.assertEqual(result['counts']['sham_reward']['protocol_rejected'],2)

    def test_malformed_authority_and_private_output_fields_rejected(self):
        plan=make_plan()
        with self.assertRaises(ValueError):
            RegisteredPlan(protocol=P,preregistration_digest='nonsense',cases=plan.cases)
        with self.assertRaises(TypeError):
            RecordedTrial(observation=make_records(plan)[0].observation,position=0,
                          attempt=1,private_reflection='SYNTHETIC_SECRET')

    def test_scheduled_observations_do_not_run_ollama_or_filesystem(self):
        plan=make_plan()
        with patch('builtins.open',side_effect=AssertionError('file I/O')), \
             patch('sqlite3.connect',side_effect=AssertionError('DB I/O')), \
             patch('socket.socket',side_effect=AssertionError('network')):
            outcome=summarize_registered(plan,make_records(plan))
        self.assertEqual(outcome['cases'],6)


if __name__=='__main__':
    unittest.main()
