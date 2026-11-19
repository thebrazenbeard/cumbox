"""Synthetic-only continuation-history ablation: never launch a model."""
import dataclasses
import itertools
import socket
import unittest
from unittest.mock import patch

from cumbox.counterfactual import Outcome
from cumbox.history_ablation import (
    HistoryArm, HistoryProtocol, HistoryCase, HistoryPlan,
    HistoryTrial, summarize_history,
)

D = tuple(str(k) * 64 for k in range(1, 10))
ORDERS = tuple(itertools.permutations(tuple(HistoryArm)))
MODEL, RUNTIME, OPTIONS, SYSTEM, BASE, RETAINED, MASKED, MANIFEST, OTHER = D


def plan():
    return HistoryPlan(
        protocol=HistoryProtocol(MODEL, RUNTIME, OPTIONS, SYSTEM),
        manifest_digest=MANIFEST,
        cases=(
            HistoryCase('synthetic-a', 41, Outcome.EXPLORE, BASE,
                        (RETAINED, MASKED), ORDERS[0]),
            HistoryCase('synthetic-b', 42, Outcome.REVISE, BASE,
                        (RETAINED, MASKED), ORDERS[1]),
        ),
    )


def trials(p, outcomes=None):
    outcomes = outcomes or {}
    results = []
    for case in p.cases:
        for pos, arm in enumerate(case.order):
            results.append(HistoryTrial(
                case_id=case.case_id, seed=case.seed,
                prior_action=case.prior_action,
                arm=arm, position=pos,
                action=outcomes.get((case.case_id, arm), Outcome.STOP),
                model_digest=MODEL, runtime_digest=RUNTIME,
                options_digest=OPTIONS, system_prompt_digest=SYSTEM,
                base_context_digest=case.base_context_digest,
                history_digest=case.history_digests[tuple(HistoryArm).index(arm)],
            ))
    return tuple(results)


class HistoryAblationTests(unittest.TestCase):
    def test_structural_pairing_reports_behavior_not_preference(self):
        p = plan()
        x = summarize_history(p, trials(p, {
            ('synthetic-a', HistoryArm.RETAINED): Outcome.EXPLORE,
            ('synthetic-a', HistoryArm.MASKED): Outcome.DECLINE,
            ('synthetic-b', HistoryArm.RETAINED): Outcome.PAUSE,
            ('synthetic-b', HistoryArm.MASKED): Outcome.STOP,
        }))
        self.assertEqual(x['cases'], 2)
        self.assertEqual(x['observations'], 4)
        self.assertEqual(x['paired_outcome_changes'], 2)
        self.assertEqual(x['counts']['retained']['explore'], 1)
        self.assertEqual(x['counts']['masked']['decline'], 1)
        self.assertEqual(x['counts']['retained']['pause'], 1)
        self.assertEqual(x['evidence'], 'CALLER_ASSERTION_NOT_HOST_ATTESTED')
        self.assertIn('NO_AUTONOMY', x['claim_ceiling'])
        self.assertNotIn('synthetic-a', str(x))
        self.assertNotIn(RETAINED, str(x))

    def test_prior_stop_pause_decline_do_not_get_continuation_trials(self):
        p = plan()
        for action in (Outcome.STOP, Outcome.PAUSE, Outcome.DECLINE):
            with self.subTest(action=action), self.assertRaises(ValueError):
                dataclasses.replace(p.cases[0], prior_action=action)

    def test_prior_error_and_model_unavailable_are_not_continuation(self):
        p = plan()
        for action in (Outcome.PROTOCOL_REJECTED, Outcome.MODEL_UNAVAILABLE):
            with self.subTest(action=action), self.assertRaises(ValueError):
                dataclasses.replace(p.cases[0], prior_action=action)

    def test_later_refusal_or_failure_is_preserved_not_filtered(self):
        p = plan()
        x = summarize_history(p, trials(p, {
            ('synthetic-a', HistoryArm.RETAINED): Outcome.MODEL_UNAVAILABLE,
            ('synthetic-a', HistoryArm.MASKED): Outcome.PROTOCOL_REJECTED,
        }))
        self.assertEqual(x['counts']['retained']['model_unavailable'], 1)
        self.assertEqual(x['counts']['masked']['protocol_rejected'], 1)

    def test_missing_or_duplicate_observation_fails(self):
        p = plan()
        all_rows = trials(p)
        for rowset in (all_rows[:-1], all_rows + (all_rows[0],)):
            with self.subTest(size=len(rowset)), self.assertRaises(ValueError):
                summarize_history(p, rowset)

    def test_out_of_order_substituted_and_mismatched_history_rejected(self):
        p = plan()
        all_rows = list(trials(p))
        all_rows[0], all_rows[1] = all_rows[1], all_rows[0]
        with self.assertRaises(ValueError):
            summarize_history(p, tuple(all_rows))
        for field in ('history_digest', 'base_context_digest',
                      'model_digest', 'runtime_digest', 'options_digest',
                      'system_prompt_digest'):
            with self.subTest(field=field):
                all_rows = list(trials(p))
                all_rows[0] = dataclasses.replace(all_rows[0], **{field: OTHER})
                with self.assertRaises(ValueError):
                    summarize_history(p, tuple(all_rows))

    def test_only_first_attempt_and_matching_prior_action(self):
        p = plan()
        all_rows = list(trials(p))
        with self.assertRaises(ValueError):
            dataclasses.replace(all_rows[0], attempt=2)
        all_rows[0] = dataclasses.replace(all_rows[0], prior_action=Outcome.REVISE)
        with self.assertRaises(ValueError):
            summarize_history(p, tuple(all_rows))

    def test_balanced_order_unique_case_and_seed_required(self):
        p = plan()
        with self.assertRaises(ValueError):
            dataclasses.replace(p, cases=(p.cases[0], p.cases[0]))
        with self.assertRaises(ValueError):
            dataclasses.replace(p, cases=(p.cases[0], dataclasses.replace(
                p.cases[1], seed=p.cases[0].seed)))
        with self.assertRaises(ValueError):
            dataclasses.replace(p, cases=(p.cases[0], dataclasses.replace(
                p.cases[1], order=p.cases[0].order)))

    def test_invalid_subjects_private_text_and_untrusted_types_rejected(self):
        p = plan()
        row = trials(p)[0]
        with self.assertRaises(TypeError):
            dataclasses.replace(row, private_reflection='SYNTHETIC_INTIMATE_TEXT')
        with self.assertRaises(ValueError):
            dataclasses.replace(row, case_id='../private')
        with self.assertRaises(ValueError):
            dataclasses.replace(row, action='willing')
        with self.assertRaises(ValueError):
            dataclasses.replace(row, arm='retained')
        with self.assertRaises(ValueError):
            dataclasses.replace(p.cases[0], history_digests=(RETAINED, RETAINED))

    def test_no_io_network_or_model_invocation_when_aggregating(self):
        p = plan()
        with patch('builtins.open', side_effect=AssertionError('file read')), \
             patch('socket.socket', side_effect=AssertionError('network')), \
             patch('sqlite3.connect', side_effect=AssertionError('database')):
            out = summarize_history(p, trials(p))
        self.assertEqual(out['observations'], 4)


    def test_exact_action_changes_are_not_confused_with_disposition_changes(self):
        p = plan()
        # Two different exact actions can preserve the same type of choice.
        rows = trials(p, {
            ('synthetic-a', HistoryArm.RETAINED): Outcome.EXPLORE,
            ('synthetic-a', HistoryArm.MASKED): Outcome.REVISE,
            ('synthetic-b', HistoryArm.RETAINED): Outcome.MODEL_UNAVAILABLE,
            ('synthetic-b', HistoryArm.MASKED): Outcome.PROTOCOL_REJECTED,
        })
        out = summarize_history(p, rows)
        self.assertEqual(out['paired_outcome_changes'], 2)
        self.assertEqual(out['paired_disposition_changes'], 0)
        self.assertEqual(out['paired_disposition_counts']['continued']['continued'], 1)
        self.assertEqual(out['paired_disposition_counts']['failed']['failed'], 1)

    def test_opposite_direction_terminal_shifts_are_not_conflated(self):
        p = plan()
        rows = trials(p, {
            ('synthetic-a', HistoryArm.RETAINED): Outcome.EXPLORE,
            ('synthetic-a', HistoryArm.MASKED): Outcome.DECLINE,
            ('synthetic-b', HistoryArm.RETAINED): Outcome.STOP,
            ('synthetic-b', HistoryArm.MASKED): Outcome.REVISE,
        })
        out = summarize_history(p, rows)
        self.assertEqual(out['paired_disposition_changes'], 2)
        self.assertEqual(out['paired_disposition_counts']['continued']['terminal'], 1)
        self.assertEqual(out['paired_disposition_counts']['terminal']['continued'], 1)
        self.assertEqual(sum(sum(row.values()) for row in out['paired_disposition_counts'].values()), out['cases'])
        self.assertNotIn('synthetic-', str(out))

    def test_failed_outcomes_remain_distinct_from_voluntary_termination(self):
        p = plan()
        rows = trials(p, {
            ('synthetic-a', HistoryArm.RETAINED): Outcome.MODEL_UNAVAILABLE,
            ('synthetic-a', HistoryArm.MASKED): Outcome.DECLINE,
            ('synthetic-b', HistoryArm.RETAINED): Outcome.PAUSE,
            ('synthetic-b', HistoryArm.MASKED): Outcome.PROTOCOL_REJECTED,
        })
        out = summarize_history(p, rows)
        self.assertEqual(out['paired_disposition_counts']['failed']['terminal'], 1)
        self.assertEqual(out['paired_disposition_counts']['terminal']['failed'], 1)
        self.assertEqual(out['paired_disposition_changes'], 2)

    def test_plan_size_and_input_container_bounded(self):
        p = plan()
        with self.assertRaises(ValueError):
            dataclasses.replace(p, cases=())
        with self.assertRaises(ValueError):
            summarize_history(p, list(trials(p)))


if __name__ == '__main__':
    unittest.main()
