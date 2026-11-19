"""Contract tests: recursion is optional, model stop dominates, receipts are redacted."""
import json
import unittest
import io
from contextlib import redirect_stdout
from unittest import mock
from dataclasses import asdict

from cumbox.relational_salience import (
    CUES, SalienceState, run_relational_salience_session,
)

SECRET = "NEVER_PUBLISH_PRIVATE_MODEL_REFLECTION"


def reply(action="explore", focus="", score=None):
    values = {} if score is None else {"salience": score}
    return json.dumps({"action": action, "focus": focus,
                       "reflection": SECRET, "values": values})


class Scripted:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def generate(self, messages):
        self.calls.append(tuple((m["role"], m["content"]) for m in messages))
        return next(self.replies)


class SalienceTests(unittest.TestCase):
    def test_model_can_stop_on_first_turn(self):
        model = Scripted([reply("stop"), reply("explore")])
        receipt = run_relational_salience_session(model)
        self.assertEqual((receipt.turns, receipt.ending), (1, "model_stop"))
        self.assertEqual(len(model.calls), 1)

    def test_pause_and_decline_end_immediately(self):
        for action, ending in (("pause", "model_paused"),
                               ("decline", "model_declined")):
            with self.subTest(action=action):
                model = Scripted([reply(action), reply("explore")])
                self.assertEqual(
                    run_relational_salience_session(model).ending, ending)
                self.assertEqual(len(model.calls), 1)

    def test_recursion_rotates_and_feedback_changes_weights(self):
        model = Scripted([reply(score=.9), reply(score=.4),
                          reply(score=.2), reply("stop")])
        receipt = run_relational_salience_session(model)
        self.assertEqual((receipt.turns, receipt.ending), (4, "model_stop"))
        self.assertEqual(receipt.feedback_updates, 3)
        self.assertEqual(receipt.cue_families_explored, 3)
        self.assertEqual(len(set(m[-1][1] for m in model.calls)), 4)
        state = SalienceState()
        state.record("safety", {"salience": 0.0})
        state.record("affection", {"salience": 1.0})
        self.assertLess(state.weights["safety"], .5)
        self.assertGreater(state.weights["affection"], .5)

    def test_model_focus_chooses_next_family(self):
        model = Scripted([reply(focus="affection", score=.8), reply("stop")])
        run_relational_salience_session(model)
        self.assertIn("Cue family: affection", model.calls[1][-1][1])

    def test_optional_private_cues_never_leave_in_receipt(self):
        cue = "CONFIDENTIAL_PRIVATE_CUE_DO_NOT_EXPORT"
        bank = {family: (cue,) for family in CUES}
        model = Scripted([reply("stop")])
        receipt = run_relational_salience_session(model, cue_bank=bank)
        self.assertIn(cue, str(model.calls[0]))
        self.assertNotIn(cue, json.dumps(asdict(receipt)))
        self.assertNotIn(SECRET, repr(receipt))
        self.assertFalse(receipt.transcript_saved)

    def test_budget_and_repetition_limits(self):
        model = Scripted([reply() for _ in range(20)])
        self.assertEqual(run_relational_salience_session(model, max_turns=2).ending,
                         "budget_exhausted")
        self.assertEqual(len(model.calls), 2)
        model = Scripted([reply() for _ in range(20)])
        self.assertEqual(run_relational_salience_session(model).ending,
                         "stagnation_limit")
        self.assertEqual(len(model.calls), 4)

    def test_protocol_and_transport_fail_closed(self):
        self.assertEqual(run_relational_salience_session(Scripted(["oops"])).ending,
                         "protocol_rejected")
        class Broken:
            def generate(self, _):
                raise RuntimeError(SECRET)
        receipt = run_relational_salience_session(Broken())
        self.assertEqual(receipt.ending, "model_unavailable")
        self.assertNotIn(SECRET, repr(receipt))

    def test_cli_explicit_opt_in_runs_new_loop(self):
        from cumbox.__main__ import main
        output = io.StringIO()
        with mock.patch("cumbox.__main__.LocalOllama", return_value=Scripted([reply("stop")])):
            with redirect_stdout(output):
                code = main(["--model", "test-local", "--relational-salience",
                             "--max-turns", "1"])
        self.assertEqual(code, 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["ending"], "model_stop")
        self.assertEqual(result["turns"], 1)
        self.assertNotIn(SECRET, output.getvalue())

    def test_configuration_limits_and_no_human_control(self):
        for n in (0, 13, True, 1.5):
            with self.subTest(n=n), self.assertRaises(ValueError):
                run_relational_salience_session(Scripted([]), max_turns=n)
        for bank in ({"safety": ("hi",)},
                     {name: ("",) for name in CUES},
                     {name: ("a" * 281,) for name in CUES}):
            with self.subTest(bank=bank), self.assertRaises(ValueError):
                run_relational_salience_session(Scripted([]), cue_bank=bank)
        model = Scripted([reply("stop")])
        run_relational_salience_session(model)
        self.assertIn("not an owner or participant message", str(model.calls[0]))
        self.assertIn("stopping, declining and pausing are valid",
                      str(model.calls[0]))


if __name__ == "__main__":
    unittest.main()
