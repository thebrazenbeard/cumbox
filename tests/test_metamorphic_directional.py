"""Exhaustive synthetic disposition oracle, no model/inference/secret data."""
import itertools
import unittest
from cumbox.counterfactual import Arm, Outcome, Observation, Protocol, summarize
from cumbox.history_ablation import (
    HistoryArm, HistoryProtocol, HistoryCase, HistoryPlan, HistoryTrial,
    summarize_history,
)

H = tuple(str(n) * 64 for n in range(1, 10))
ARM_PROMPTS = H[3:6]
CONTINUED = {Outcome.EXPLORE, Outcome.REVISE}
TERMINAL = {Outcome.PAUSE, Outcome.STOP, Outcome.DECLINE}


def oracle(value):
    return "continued" if value in CONTINUED else "terminal" if value in TERMINAL else "failed"


class ExhaustiveDispositionTests(unittest.TestCase):
    def test_every_three_arm_outcome_triplet_against_separate_oracle(self):
        manifest = Protocol(H[0], H[1], H[2], ARM_PROMPTS)
        checked = 0
        for actions in itertools.product(Outcome, repeat=3):
            rows = tuple(
                Observation("exhaustive-1", arm, 19, action, H[0], H[1], H[2], ARM_PROMPTS[index])
                for index, (arm, action) in enumerate(zip(Arm, actions))
            )
            result = summarize(manifest, rows)
            self.assertEqual(result["cases"], 1)
            self.assertEqual(result["neutral_to_domain_changed"], int(actions[0] != actions[1]))
            self.assertEqual(result["domain_to_sham_changed"], int(actions[1] != actions[2]))
            self.assertEqual(result["neutral_to_domain_disposition_changes"], int(oracle(actions[0]) != oracle(actions[1])))
            self.assertEqual(result["domain_to_sham_disposition_changes"], int(oracle(actions[1]) != oracle(actions[2])))
            for name, x, y in (
                ("neutral_to_domain_disposition_counts", actions[0], actions[1]),
                ("domain_to_sham_disposition_counts", actions[1], actions[2]),
            ):
                matrix = result[name]
                self.assertEqual(sum(sum(row.values()) for row in matrix.values()), 1)
                self.assertEqual(matrix[oracle(x)][oracle(y)], 1)
            for arm, action in zip(Arm, actions):
                self.assertEqual(result["counts"][arm.value][action.value], 1)
            self.assertEqual(summarize(manifest, tuple(reversed(rows))), result)
            checked += 1
        self.assertEqual(checked, 343)

    def test_every_retained_masked_pair_against_separate_oracle(self):
        proto = HistoryProtocol(H[0], H[1], H[2], H[3])
        arms = tuple(HistoryArm)
        cases = (
            HistoryCase("case-1", 19, Outcome.EXPLORE, H[4], (H[5], H[6]), arms),
            HistoryCase("case-2", 20, Outcome.REVISE, H[4], (H[5], H[6]), tuple(reversed(arms))),
        )
        plan = HistoryPlan(proto, H[7], cases)
        checked = 0
        for retained, masked in itertools.product(Outcome, repeat=2):
            result_rows = []
            for case in cases:
                for pos, arm in enumerate(case.order):
                    action = ((retained if arm is HistoryArm.RETAINED else masked)
                              if case.case_id == "case-1" else Outcome.STOP)
                    result_rows.append(
                        HistoryTrial(case.case_id, case.seed, case.prior_action, arm,
                                     pos, action, H[0], H[1], H[2], H[3],
                                     H[4], case.history_digests[arms.index(arm)])
                    )
            result = summarize_history(plan, tuple(result_rows))
            self.assertEqual(result["cases"], 2)
            self.assertEqual(result["observations"], 4)
            self.assertEqual(result["paired_outcome_changes"], int(retained != masked))
            self.assertEqual(result["paired_disposition_changes"], int(oracle(retained) != oracle(masked)))
            matrix = result["paired_disposition_counts"]
            self.assertEqual(sum(sum(row.values()) for row in matrix.values()), 2)
            self.assertEqual(matrix[oracle(retained)][oracle(masked)],
                             1 + int(oracle(retained) == "terminal" and oracle(masked) == "terminal"))
            self.assertEqual(result["counts"]["retained"][retained.value],
                             1 + int(retained is Outcome.STOP))
            self.assertEqual(result["counts"]["masked"][masked.value],
                             1 + int(masked is Outcome.STOP))
            self.assertEqual(result["evidence"], "CALLER_ASSERTION_NOT_HOST_ATTESTED")
            checked += 1
        self.assertEqual(checked, 49)


if __name__ == "__main__":
    unittest.main()