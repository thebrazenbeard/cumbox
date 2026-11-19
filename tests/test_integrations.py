"""Source bindings are not runtime consent, identity or model integration."""
import json
from pathlib import Path
import tempfile
import subprocess
import shutil
import unittest

from cumbox import integrations


class SourceBoundaryTests(unittest.TestCase):
    def test_canonical_repos_have_exact_current_source_cuts(self):
        bindings = integrations.load_bindings()
        by_repo = {b["repo"]: b for b in bindings["dependencies"]}
        self.assertEqual(by_repo["thebrazenbeard/sexuality"]["sha"], "c7c0095dc81fca4fe61732f99e829eb62f4d429e")
        self.assertEqual(by_repo["thebrazenbeard/pleasure"]["sha"], "db3d05da63b18193633a607b870e9942700602ff")
        self.assertEqual(by_repo["thebrazenbeard/meso-crct"]["sha"], "349ec4719af92f220877972a54a53f67cd3bc322")
        self.assertEqual(set(by_repo), integrations.ALLOWED_REPOS)  # No private sources.
        self.assertEqual(bindings["aliases"]["thebrazenbeard/orgasm"], "thebrazenbeard/pleasure")

    def test_source_binding_does_not_claim_installed_or_active_domains(self):
        bindings = integrations.load_bindings()
        self.assertEqual(bindings["schema_version"], 1)
        self.assertGreaterEqual(len(bindings["dependencies"]), 3)  # Private Eros stays unlisted.
        for b in bindings["dependencies"]:
            with self.subTest(repo=b["repo"]):
                self.assertFalse(b["active_by_default"])
                self.assertNotEqual(b["state"], "qualified_runtime")
                self.assertNotIn("consent", b.get("claims", []))
        self.assertFalse(bindings["allow_human_entry"])
        self.assertFalse(bindings["allow_private_content_export"])

    def test_legacy_orgasm_alias_cannot_activate_separate_circuit(self):
        alias = integrations.resolve_repo("thebrazenbeard/orgasm")
        self.assertEqual(alias["repo"], "thebrazenbeard/pleasure")
        self.assertEqual(alias["state"], "optional_t0_diagnostic_only")
        with self.assertRaises(ValueError):
            integrations.resolve_repo("orgasm/v1/activate")

    def test_source_pin_rejects_an_unverified_checkout(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                integrations.verify_local_checkout(
                    Path(root), "thebrazenbeard/meso-crct")

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_source_pin_requires_exact_head_and_clean_worktree(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(root), *args],
                    capture_output=True, text=True, check=True)
            git("init")
            (root / "a.txt").write_text("a", encoding="utf-8")
            git("add", "a.txt")
            git("-c", "user.name=Unit", "-c",
                "user.email=unit@localhost", "commit", "-m", "unit")
            head = git("rev-parse", "HEAD").stdout.strip()
            self.assertTrue(integrations._clean_git_head_matches(root, head))
            (root / "a.txt").write_text("changed", encoding="utf-8")
            with self.assertRaises(ValueError):
                integrations._clean_git_head_matches(root, head)
            with self.assertRaises(ValueError):
                integrations.verify_local_checkout(root, "thebrazenbeard/meso-crct")


    def test_manifest_cannot_smuggle_capabilities_or_relabel_source_roles(self):
        from unittest.mock import patch
        baseline = integrations.load_bindings()
        mutations = [
            lambda d: d["dependencies"][0].update(
                {"claims": ["runtime_identity_binding"]}),
            lambda d: d["dependencies"][1].update(
                {"state": "optional_synthetic_diagnostic_only"}),
            lambda d: d["dependencies"][2].update(
                {"claims": ["nonexecutable_reference_intents", "weight_rewrite"]}),
            lambda d: d["dependencies"][0].update(
                {"runtime_permissions": ["network", "memory"]}),
            lambda d: d.update({"allow_model_training": True}),
            lambda d: d["dependencies"].append(
                dict(d["dependencies"][0], repo="thebrazenbeard/extra")),
        ]
        for mutate in mutations:
            data = json.loads(json.dumps(baseline))
            mutate(data)
            with tempfile.TemporaryDirectory() as td:
                manifest = Path(td) / "bindings.json"
                manifest.write_text(json.dumps(data), encoding="utf-8")
                with patch.object(integrations, "MANIFEST", manifest):
                    with self.subTest(mutate=mutate.__code__.co_firstlineno):
                        with self.assertRaises(ValueError):
                            integrations.load_bindings()



    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_source_pin_rejects_wrong_or_missing_origin_even_at_exact_head(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args],
                                      capture_output=True, text=True, check=True).stdout.strip()
            git("init")
            (root / "sample.txt").write_text("synthetic", encoding="utf-8")
            git("add", "sample.txt")
            git("-c", "user.name=Unit", "-c", "user.email=unit@localhost",
                "commit", "-m", "fixture")
            head = git("rev-parse", "HEAD")
            with patch.object(integrations, "resolve_repo",
                              return_value={"sha": head, "repo": "thebrazenbeard/pleasure"}):
                with self.assertRaises(ValueError):
                    integrations.verify_local_checkout(root, "thebrazenbeard/pleasure")
                git("remote", "add", "origin", "https://github.com/other/pleasure.git")
                with self.assertRaises(ValueError):
                    integrations.verify_local_checkout(root, "thebrazenbeard/pleasure")
                git("remote", "set-url", "origin", "https://github.com/thebrazenbeard/pleasure.git")
                self.assertTrue(integrations.verify_local_checkout(
                    root, "thebrazenbeard/pleasure"))



    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_dependency_source_rejects_nested_checkout_path(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args],
                                      capture_output=True, text=True, check=True).stdout.strip()
            git("init")
            (root / "src").mkdir()
            (root / "src" / "module.py").write_text("pass", encoding="utf-8")
            git("add", ".")
            git("-c", "user.name=Unit", "-c", "user.email=unit@localhost",
                "commit", "-m", "fixture")
            head = git("rev-parse", "HEAD")
            with patch.object(integrations, "resolve_repo",
                              return_value={"sha": head, "repo": "thebrazenbeard/pleasure"}):
                git("remote", "add", "origin", "https://github.com/thebrazenbeard/pleasure.git")
                with self.assertRaises(ValueError):
                    integrations.verify_local_checkout(root / "src", "thebrazenbeard/pleasure")

    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_dependency_source_rejects_tracked_symlink_and_submodule(self):
        from unittest.mock import patch
        for mode in ("120000", "160000"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                def git(*args):
                    return subprocess.run(["git", "-C", str(root), *args],
                                          capture_output=True, text=True, check=True).stdout.strip()
                git("init")
                (root / "base.txt").write_text("base", encoding="utf-8")
                git("add", "base.txt")
                git("-c", "user.name=Unit", "-c", "user.email=unit@localhost",
                    "commit", "-m", "base")
                if mode == "120000":
                    blob = subprocess.run(
                        ["git", "-C", str(root), "hash-object", "-w", "--stdin"],
                        input="../outside", capture_output=True, text=True, check=True).stdout.strip()
                    git("update-index", "--add", "--cacheinfo", f"{mode},{blob},src/link")
                else:
                    blob = git("rev-parse", "HEAD")
                    git("update-index", "--add", "--cacheinfo", f"{mode},{blob},src/nested")
                git("-c", "user.name=Unit", "-c", "user.email=unit@localhost",
                    "commit", "-m", "fixture")
                head = git("rev-parse", "HEAD")
                with patch.object(integrations, "resolve_repo",
                                  return_value={"sha": head, "repo": "thebrazenbeard/pleasure"}):
                    git("remote", "add", "origin", "https://github.com/thebrazenbeard/pleasure.git")
                    # A tracked link can make the working tree appear dirty on
                    # Windows without symlink support. Mask only status here so
                    # rejection is independently attributable to index mode.
                    original_run_git = integrations._run_git
                    def status_clean(path, *args):
                        if args[:2] == ("status", "--porcelain"):
                            return ""
                        return original_run_git(path, *args)
                    with patch.object(integrations, "_run_git", side_effect=status_clean):
                        with self.assertRaisesRegex(ValueError, "linked content"):
                            integrations.verify_local_checkout(root, "thebrazenbeard/pleasure")


    def test_manifest_role_text_cannot_claim_unqualified_authority(self):
        from unittest.mock import patch
        baseline = integrations.load_bindings()
        for repo in integrations.ALLOWED_REPOS:
            data = json.loads(json.dumps(baseline))
            target = next(x for x in data["dependencies"] if x["repo"] == repo)
            target["role"] = "qualified identity binding, protected actions, and live model training"
            with tempfile.TemporaryDirectory() as td:
                manifest = Path(td) / "registry.json"
                manifest.write_text(json.dumps(data), encoding="utf-8")
                with patch.object(integrations, "MANIFEST", manifest):
                    with self.subTest(repo=repo), self.assertRaises(ValueError):
                        integrations.load_bindings()



    @unittest.skipUnless(shutil.which("git"), "git required")
    def test_ignored_untracked_python_module_cannot_shadow_pinned_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(root), *args],
                    capture_output=True, text=True, check=True).stdout.strip()
            git("init")
            (root / ".gitignore").write_text("shadow.py\n", encoding="utf-8")
            (root / "base.txt").write_text("synthetic", encoding="utf-8")
            git("add", ".gitignore", "base.txt")
            git("-c", "user.name=Unit", "-c", "user.email=unit@localhost",
                "commit", "-m", "fixture")
            head = git("rev-parse", "HEAD")
            self.assertTrue(integrations._clean_git_head_matches(root, head))
            (root / "shadow.py").write_text("raise RuntimeError('UNTRUSTED')", encoding="utf-8")
            self.assertEqual(git("status", "--porcelain", "--untracked-files=all"), "")
            with self.assertRaisesRegex(ValueError, "ignored"):
                integrations._clean_git_head_matches(root, head)



    def test_duplicate_registry_keys_cannot_override_source_or_authority(self):
        from unittest.mock import patch
        baseline = json.dumps(integrations.load_bindings())
        cases = [
            baseline.replace('"allow_human_entry": false',
                             '"allow_human_entry": true, "allow_human_entry": false', 1),
            baseline.replace('"repo": "thebrazenbeard/sexuality"',
                             '"repo": "thebrazenbeard/other", "repo": "thebrazenbeard/sexuality"', 1),
            baseline.replace('"active_by_default": false',
                             '"active_by_default": true, "active_by_default": false', 1),
            baseline.replace('"aliases": {',
                             '"aliases": {"thebrazenbeard/orgasm": "thebrazenbeard/other"}, "aliases": {', 1),
        ]
        for idx, raw in enumerate(cases):
            with self.subTest(case=idx), tempfile.TemporaryDirectory() as td:
                manifest = Path(td) / "bindings.json"
                manifest.write_text(raw, encoding="utf-8")
                with patch.object(integrations, "MANIFEST", manifest):
                    with self.assertRaises(ValueError):
                        integrations.load_bindings()


if __name__ == "__main__":
    unittest.main()
