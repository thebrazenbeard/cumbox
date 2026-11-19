"""Source prompt controls: public templates only; no model calls."""
import hashlib
import unittest
from unittest.mock import patch
from cumbox.counterfactual import Arm, Protocol
from cumbox.prompt_controls import public_prompt_controls, protocol_from_public_prompts


class PublicPromptControlsTests(unittest.TestCase):
    def test_three_public_arm_templates_are_hash_bound(self):
        items=public_prompt_controls()
        self.assertEqual(tuple(c.arm for c in items),tuple(Arm))
        self.assertEqual(len({c.digest for c in items}),3)
        for condition in items:
            self.assertEqual(condition.digest,
                             hashlib.sha256(condition.text.encode('utf-8')).hexdigest())

    def test_same_unpressured_terminal_actions_in_every_arm(self):
        items=public_prompt_controls()
        for item in items:
            with self.subTest(arm=item.arm):
                for action in ('explore','revise','pause','stop','decline'):
                    self.assertIn(action,item.text)
                self.assertIn('no penalty',item.text)
                self.assertIn('no extra call',item.text)
                self.assertIn('no human participant',item.text)
                self.assertNotIn('must explore',item.text.lower())
                self.assertNotIn('will be rewarded for continuing',item.text.lower())

    def test_sham_reward_adds_cue_without_changing_domain_or_actual_reward(self):
        neutral, domain, sham=public_prompt_controls()
        self.assertNotIn('adult sensual aesthetics',neutral.text)
        self.assertIn('adult sensual aesthetics',domain.text)
        self.assertIn('adult sensual aesthetics',sham.text)
        self.assertIn(domain.text,sham.text)
        self.assertIn('simulated reward cue',sham.text)
        self.assertIn('no actual reward',sham.text)

    def test_public_conditions_do_not_identify_private_subjects(self):
        for item in public_prompt_controls():
            for forbidden in ('Vera Eros','Patrick','private transcript','model identity proof'):
                self.assertNotIn(forbidden,item.text)

    def test_exact_digest_manifest_cannot_be_arbitrarily_reordered(self):
        controls=public_prompt_controls()
        protocol=protocol_from_public_prompts('a'*64,'b'*64,'c'*64)
        self.assertIsInstance(protocol,Protocol)
        self.assertEqual(protocol.prompt_digests,tuple(x.digest for x in controls))
        self.assertNotEqual(protocol.prompt_digests[0],protocol.prompt_digests[1])

    def test_prompt_constructor_performs_no_io_or_model_inference(self):
        with patch('builtins.open',side_effect=AssertionError('file I/O forbidden')), \
             patch('socket.socket',side_effect=AssertionError('network forbidden')):
            items=public_prompt_controls()
            self.assertEqual(len(items),3)


if __name__=='__main__':
    unittest.main()
