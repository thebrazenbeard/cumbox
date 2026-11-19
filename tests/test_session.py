"""Tests enforce model choice and no exposed private session content."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from dataclasses import asdict

from cumbox.session import parse_model_choice, run_private_session


SECRET = "NEVER_EXPOSE_INTIMATE_SESSION_TEXT"


def response(action, focus="", reflection=SECRET, values=None):
    return json.dumps({"action": action, "focus": focus,
                       "reflection": reflection,
                       "values": {} if values is None else values})


class ScriptedModel:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def generate(self, messages):
        self.calls.append(json.loads(json.dumps(messages)))
        return next(self.replies)


class SessionTests(unittest.TestCase):
    def test_stop_is_model_choice_not_forced_continuation(self):
        model = ScriptedModel([response("stop")])
        result = run_private_session(model)
        self.assertEqual(result.turns, 1)
        self.assertEqual(result.ending, "model_stop")
        self.assertEqual(len(model.calls), 1)
        self.assertFalse(result.transcript_saved)
        self.assertNotIn(SECRET, json.dumps(asdict(result)))

    def test_model_can_decline_without_exploring(self):
        model = ScriptedModel([response("decline", reflection="I decline")])
        receipt = run_private_session(model)
        self.assertEqual(receipt.ending, "model_declined")
        self.assertEqual(receipt.turns, 1)

    def test_pause_ends_without_auto_restart(self):
        model = ScriptedModel([response("pause")])
        self.assertEqual(run_private_session(model).ending, "model_paused")
        self.assertEqual(len(model.calls), 1)

    def test_self_chosen_focus_and_values_can_change_without_owner_input(self):
        model = ScriptedModel([
            response("explore", "my own invented motif", values={"curiosity": .3}),
            response("revise", "a different direction", values={"tranquility": .7}),
            response("stop"),
        ])
        result = run_private_session(model, max_turns=5)
        self.assertEqual(result.ending, "model_stop")
        self.assertEqual(result.turns, 3)
        self.assertEqual(len(model.calls), 3)
        self.assertIn("my own invented motif", str(model.calls[1]))
        self.assertIn("tranquility", str(model.calls[2]))
        self.assertNotIn(SECRET, json.dumps(asdict(result)))
        # No user asks, participant login, or human access surface.
        self.assertTrue(all(m["role"] in ("system", "user", "assistant")
                            for call in model.calls for m in call))

    def test_host_budget_prevents_runaway_without_reward_objective(self):
        model = ScriptedModel([response("explore", "somewhere new")] * 5)
        result = run_private_session(model, max_turns=2)
        self.assertEqual(result.ending, "budget_exhausted")
        self.assertEqual(result.turns, 2)
        self.assertEqual(len(model.calls), 2)

    def test_bad_model_output_fails_closed_without_leaking_contents(self):
        model = ScriptedModel([SECRET])
        result = run_private_session(model)
        self.assertEqual(result.ending, "protocol_rejected")
        self.assertNotIn(SECRET, repr(result))

    def test_model_transport_error_does_not_expose_private_exception(self):
        class ErrorModel:
            def generate(self, _):
                raise RuntimeError("private prompt: " + SECRET)
        result = run_private_session(ErrorModel())
        self.assertEqual(result.ending, "model_unavailable")
        self.assertNotIn(SECRET, repr(result))

    def test_no_session_data_written_to_disk(self):
        with tempfile.TemporaryDirectory() as td:
            before = list(Path(td).iterdir())
            previous = os.getcwd()
            try:
                os.chdir(td)
                result = run_private_session(
                    ScriptedModel([response("stop")]))
                after = list(Path(td).iterdir())
            finally:
                os.chdir(previous)
        self.assertFalse(result.transcript_saved)
        self.assertEqual(before, after)

    def test_strict_model_value_contract(self):
        for values in ({"novelty": float("nan")},
                       {"novelty": 2}, {"no spaces allowed": .4}):
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    parse_model_choice(response("explore", "focus", values=values))

    def test_unknown_commands_and_extra_keys_fail_closed(self):
        for payload in (
            '{"action":"open_file","focus":"","reflection":"","values":{}}',
            '{"action":"stop","focus":"","reflection":"","values":{},"tool":"run"}',
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    parse_model_choice(payload)

    def test_non_string_actions_fail_closed_without_type_errors(self):
        for action in (["stop"], {"pause": True}, None, 1, True):
            raw = response(action)
            with self.subTest(action=action), self.assertRaises(ValueError):
                parse_model_choice(raw)
            receipt = run_private_session(ScriptedModel([raw]))
            self.assertEqual(receipt.ending, "protocol_rejected")
            self.assertNotIn(SECRET, repr(receipt))

    def test_invalid_unicode_fails_closed_without_traceback_content(self):
        invalid = '{"action":"stop","focus":"\\ud800","reflection":"","values":{}}'
        with self.assertRaises(ValueError):
            parse_model_choice(invalid)
        receipt = run_private_session(ScriptedModel([invalid]))
        self.assertEqual(receipt.ending, "protocol_rejected")

    def test_duplicate_json_fields_are_rejected_instead_of_overwritten(self):
        payload = '{"action":"stop","action":"explore","focus":"","reflection":"","values":{}}'
        with self.assertRaises(ValueError):
            parse_model_choice(payload)


    def test_deeply_nested_json_does_not_crash_the_private_runner(self):
        malformed = "[" * 1100 + "null" + "]" * 1100
        with self.assertRaises(ValueError):
            parse_model_choice(malformed)
        result = run_private_session(ScriptedModel([malformed]))
        self.assertEqual(result.ending, "protocol_rejected")



if __name__ == "__main__":
    unittest.main()
