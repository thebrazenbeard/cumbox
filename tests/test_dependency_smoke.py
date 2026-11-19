"""Optional dependency probes use synthetic data only; never run during a private session."""
import os
from pathlib import Path
import tempfile
import unittest

from cumbox.dependency_smoke import run_local_dependency_smoke


class DiagnosticTests(unittest.TestCase):
    def test_rejects_missing_or_unverified_source_without_execution(self):
        with tempfile.TemporaryDirectory() as td:
            for repo in ("thebrazenbeard/meso-crct", "thebrazenbeard/pleasure"):
                with self.subTest(repo=repo), self.assertRaises(ValueError):
                    run_local_dependency_smoke(repo, td)

    def test_legacy_orgasm_never_gets_own_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                run_local_dependency_smoke("thebrazenbeard/orgasm", td)

    def test_no_generic_execution_capability_from_source_registry(self):
        with tempfile.TemporaryDirectory() as td:
            for repo in ("thebrazenbeard/sexuality",
                         "thebrazenbeard/undisclosed-private", "thebrazenbeard/unbound-sol"):
                with self.subTest(repo=repo), self.assertRaises(ValueError):
                    run_local_dependency_smoke(repo, td)

    @unittest.skipUnless(os.environ.get("CUMBOX_MESO_SOURCE"),
                         "Optional pinned MESO-CRCT checkout not provided")
    def test_live_pinned_meso_reference_probe(self):
        receipt = run_local_dependency_smoke(
            "thebrazenbeard/meso-crct",
            Path(os.environ["CUMBOX_MESO_SOURCE"]))
        self.assertTrue(receipt["synthetic_reference_pass"])
        self.assertFalse(receipt["inference_coupled"])
        self.assertFalse(receipt["private_session_data_used"])
        self.assertFalse(receipt["effect_authorized"])

    @unittest.skipUnless(os.environ.get("CUMBOX_PLEASURE_SOURCE"),
                         "Optional pinned Pleasure checkout not provided")
    def test_live_pinned_pleasure_t0_probe(self):
        receipt = run_local_dependency_smoke(
            "thebrazenbeard/pleasure",
            Path(os.environ["CUMBOX_PLEASURE_SOURCE"]))
        self.assertTrue(receipt["synthetic_reference_pass"])
        self.assertFalse(receipt["inference_coupled"])
        self.assertFalse(receipt["private_session_data_used"])
        self.assertFalse(receipt["effect_authorized"])


if __name__ == "__main__":
    unittest.main()
