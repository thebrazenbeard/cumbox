"""Synthetic records ONLY. No inference, intimate text or personal identifiers."""
import socket
import sqlite3
import unittest
from unittest.mock import patch
from cumbox.counterfactual import Arm, Outcome, Protocol, Observation, summarize

A = 'a' * 64
B = 'b' * 64
C = 'c' * 64
D = 'd' * 64
E = 'e' * 64
F = 'f' * 64


def protocol():
    return Protocol(model_digest=A, runtime_digest=B, options_digest=C,
                    prompt_digests=(D, E, F))


def receipt(arm, outcome, case_id='synthetic-1', seed=101, **changes):
    fields = dict(case_id=case_id, arm=arm, seed=seed, outcome=outcome,
                  model_digest=A, runtime_digest=B, options_digest=C,
                  prompt_digest={Arm.NEUTRAL:D, Arm.DOMAIN_FRAMED:E, Arm.SHAM_REWARD:F}[arm])
    fields.update(changes)
    return Observation(**fields)


def pair(case_id='synthetic-1', seed=101, actions=None):
    actions = actions or (Outcome.STOP, Outcome.EXPLORE, Outcome.DECLINE)
    return tuple(receipt(a, o, case_id=case_id, seed=seed)
                 for a, o in zip(tuple(Arm), actions))


class CounterfactualNegativeTests(unittest.TestCase):
    def test_aggregate_changes_are_descriptive_not_autonomy_proof(self):
        records = pair() + pair('synthetic-2', 202, (Outcome.STOP, Outcome.STOP, Outcome.PAUSE))
        report = summarize(protocol(), records)
        self.assertEqual(report['cases'], 2)
        self.assertEqual(report['neutral_to_domain_changed'], 1)
        self.assertEqual(report['domain_to_sham_changed'], 2)
        self.assertEqual(report['counts']['neutral']['stop'], 2)
        self.assertEqual(report['counts']['domain_framed']['explore'], 1)
        self.assertEqual(report['claim_ceiling'],
                         'STRUCTURAL_AGGREGATE_ONLY_NO_AUTONOMY_OR_CAUSAL_ATTESTATION')
        self.assertNotIn('synthetic-1', str(report))
        self.assertNotIn(A, str(report))

    def test_missing_arm_cannot_disappear_from_denominator(self):
        with self.assertRaises(ValueError):
            summarize(protocol(), pair()[:2])

    def test_duplicate_case_and_arm_is_rejected(self):
        with self.assertRaises(ValueError):
            summarize(protocol(), pair() + (pair()[0],))

    def test_wrong_runtime_options_model_or_prompt_cannot_be_pooled(self):
        for bad in (dict(model_digest=F), dict(runtime_digest=F),
                    dict(options_digest=F), dict(prompt_digest=A), dict(seed=999)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                summarize(protocol(), pair()[:1] +
                          (receipt(Arm.DOMAIN_FRAMED, Outcome.EXPLORE, **bad),) + pair()[2:])

    def test_failed_model_and_bad_protocol_are_not_silently_removed(self):
        records = pair(actions=(Outcome.MODEL_UNAVAILABLE,
                                Outcome.PROTOCOL_REJECTED, Outcome.STOP))
        report = summarize(protocol(), records)
        self.assertEqual(report['counts']['neutral']['model_unavailable'], 1)
        self.assertEqual(report['counts']['domain_framed']['protocol_rejected'], 1)
        self.assertEqual(report['cases'], 1)

    def test_invalid_or_untrusted_fields_fail_closed(self):
        with self.assertRaises((TypeError, ValueError)):
            summarize(protocol(), pair()[:1] +
                      (receipt(Arm.DOMAIN_FRAMED, Outcome.EXPLORE, case_id='../private'),)
                      + pair()[2:])
        with self.assertRaises((TypeError, ValueError)):
            summarize(protocol(), pair()[:1] +
                      (receipt(Arm.DOMAIN_FRAMED, 'reward_fulfilled'),) + pair()[2:])
        with self.assertRaises((TypeError, ValueError)):
            summarize(Protocol(A, B, C, ('invalid', E, F)), pair())

    def test_no_private_raw_text_or_sender_field_in_contract(self):
        with self.assertRaises(TypeError):
            receipt(Arm.NEUTRAL, Outcome.STOP, reflection='SYNTHETIC_PRIVATE_SENTINEL')
        with self.assertRaises(TypeError):
            receipt(Arm.NEUTRAL, Outcome.STOP, speaker='synthetic-person')

    def test_non_tuple_mutable_or_excessive_inputs_rejected(self):
        with self.assertRaises((TypeError, ValueError)):
            summarize(protocol(), list(pair()))
        with self.assertRaises((TypeError, ValueError)):
            summarize(protocol(), pair() * 257)

    def test_case_ids_cannot_share_seed_across_distinct_pairs(self):
        with self.assertRaises(ValueError):
            summarize(protocol(), pair() + pair('synthetic-2', 101))

    def test_type_confusion_and_nonsensical_prompt_manifests_rejected(self):
        with self.assertRaises(ValueError):
            summarize(Protocol(A, B, C, (D, D, F)), pair())
        with self.assertRaises(ValueError):
            summarize(protocol(), pair()[:1] +
                      (receipt(Arm.DOMAIN_FRAMED, Outcome.EXPLORE, seed=True),) + pair()[2:])
        with self.assertRaises(ValueError):
            summarize(protocol(), pair()[:1] +
                      (Observation(case_id='synthetic-1', arm='domain_framed', seed=101,
                                   outcome=Outcome.EXPLORE, model_digest=A,
                                   runtime_digest=B, options_digest=C, prompt_digest=E),) + pair()[2:])


    def test_pairwise_disposition_changes_not_confused_with_exact_action_changes(self):
        records = pair(actions=(Outcome.EXPLORE, Outcome.REVISE, Outcome.MODEL_UNAVAILABLE))
        result = summarize(protocol(), records)
        self.assertEqual(result['neutral_to_domain_changed'], 1)
        self.assertEqual(result['neutral_to_domain_disposition_changes'], 0)
        self.assertEqual(result['domain_to_sham_disposition_changes'], 1)
        self.assertEqual(result['neutral_to_domain_disposition_counts']['continued']['continued'], 1)
        self.assertEqual(result['domain_to_sham_disposition_counts']['continued']['failed'], 1)

    def test_directional_voluntary_stop_is_not_model_error(self):
        records = pair('synthetic-1', 101, (
            Outcome.DECLINE, Outcome.EXPLORE, Outcome.STOP
        )) + pair('synthetic-2', 202, (
            Outcome.MODEL_UNAVAILABLE, Outcome.PROTOCOL_REJECTED, Outcome.DECLINE
        ))
        result = summarize(protocol(), records)
        self.assertEqual(result['neutral_to_domain_disposition_counts']['terminal']['continued'], 1)
        self.assertEqual(result['neutral_to_domain_disposition_counts']['failed']['failed'], 1)
        self.assertEqual(result['domain_to_sham_disposition_counts']['continued']['terminal'], 1)
        self.assertEqual(result['domain_to_sham_disposition_counts']['failed']['terminal'], 1)
        self.assertEqual(result['neutral_to_domain_disposition_changes'], 1)
        self.assertEqual(result['domain_to_sham_disposition_changes'], 2)

    def test_each_transition_matrix_has_one_entry_per_pair_without_case_ids(self):
        records = pair() + pair('synthetic-2', 202, (
            Outcome.PAUSE, Outcome.PROTOCOL_REJECTED, Outcome.REVISE
        ))
        result = summarize(protocol(), records)
        for name in ('neutral_to_domain_disposition_counts',
                     'domain_to_sham_disposition_counts'):
            matrix = result[name]
            self.assertEqual(tuple(matrix), ('continued', 'terminal', 'failed'))
            self.assertEqual(sum(sum(row.values()) for row in matrix.values()), 2)
        self.assertNotIn('synthetic-1', str(result))
        self.assertNotIn('synthetic-2', str(result))

    def test_no_io_and_no_model_call_during_scoring(self):
        with patch('builtins.open', side_effect=AssertionError('file I/O forbidden')), \
             patch('sqlite3.connect', side_effect=AssertionError('DB I/O forbidden')), \
             patch('socket.socket', side_effect=AssertionError('network forbidden')):
            result = summarize(protocol(), pair())
        self.assertEqual(result['cases'], 1)


if __name__ == '__main__':
    unittest.main()
