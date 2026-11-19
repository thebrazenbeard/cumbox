"""Verified source bindings only; never runtime grants or private-state transfer."""
import json
from pathlib import Path
import re
import subprocess


MANIFEST = Path(__file__).resolve().parents[1] / "contracts" / "REPOSITORY_BINDINGS_V1.json"
SHA = re.compile(r"^[a-f0-9]{40}$")
ALLOWED_REPOS = frozenset({"thebrazenbeard/sexuality", "thebrazenbeard/pleasure", "thebrazenbeard/meso-crct"})
EXPECTED_BINDINGS = {
    "thebrazenbeard/sexuality": ("research_contract_only", ()),
    "thebrazenbeard/pleasure": ("optional_t0_diagnostic_only", ("synthetic_T0_only",)),
    "thebrazenbeard/meso-crct": (
        "optional_synthetic_diagnostic_only", ("nonexecutable_reference_intents",)),
}
EXPECTED_ROLES = {
    "thebrazenbeard/sexuality": "public model-neutral evaluation contract; not executable adapter",
    "thebrazenbeard/pleasure": "model-agnostic bounded source-only pleasure simulator",
    "thebrazenbeard/meso-crct": "typed reward/drive/learning and adversarial source code; no runtime authority",
}
TOP_LEVEL_KEYS = frozenset({
    "schema_version", "as_of", "allow_human_entry",
    "allow_private_content_export", "dependencies", "aliases",
})
DEPENDENCY_KEYS = frozenset({
    "repo", "sha", "state", "active_by_default", "role", "claims",
})


def _strict_object(pairs):
    """Reject ambiguous JSON fields at every nesting depth."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate public registry key")
        result[key] = value
    return result


def load_bindings():
    """Read a public-safe source snapshot, fail closed on forbidden capabilities."""
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"),
                          object_pairs_hook=_strict_object)
    except (OSError, ValueError) as exc:
        raise ValueError("public source registry unavailable") from None
    if (not isinstance(data, dict) or set(data) != TOP_LEVEL_KEYS
            or type(data.get("schema_version")) is not int
            or data.get("schema_version") != 1
            or data.get("allow_human_entry") is not False
            or data.get("allow_private_content_export") is not False
            or not isinstance(data.get("dependencies"), list)
            or not isinstance(data.get("aliases"), dict)):
        raise ValueError("unsupported public binding contract")
    seen = set()
    for b in data["dependencies"]:
        if (not isinstance(b, dict) or set(b) != DEPENDENCY_KEYS
                or not isinstance(b.get("repo"), str)
                or not b["repo"].startswith("thebrazenbeard/")
                or b["repo"] in seen
                or b["repo"] not in ALLOWED_REPOS
                or not isinstance(b.get("sha"), str)
                or not SHA.fullmatch(b["sha"])
                or b.get("active_by_default") is not False
                or b.get("state") != EXPECTED_BINDINGS[b["repo"]][0]
                or b.get("role") != EXPECTED_ROLES[b["repo"]]
                or not isinstance(b.get("claims"), list)
                or tuple(b["claims"]) != EXPECTED_BINDINGS[b["repo"]][1]):
            raise ValueError("unverified or unsafe public binding")
        seen.add(b["repo"])
    if seen != ALLOWED_REPOS:
        raise ValueError("incomplete public source registry")
    if data["aliases"] != {"thebrazenbeard/orgasm": "thebrazenbeard/pleasure"}:
        raise ValueError("legacy alias must preserve Pleasure source identity")
    if data["aliases"]["thebrazenbeard/orgasm"] not in seen:
        raise ValueError("dangling legacy alias")
    return data


def resolve_repo(repo):
    """Resolve a trusted current or legacy repo without installing anything."""
    data = load_bindings()
    if not isinstance(repo, str):
        raise ValueError("unknown repository")
    canonical = data["aliases"].get(repo, repo)
    for binding in data["dependencies"]:
        if binding["repo"] == canonical:
            return dict(binding)
    raise ValueError("repository has no public source binding")


def _run_git(path, *args):
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *args], capture_output=True,
            text=True, timeout=4, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError("local source verification unavailable") from None
    if result.returncode:
        raise ValueError("local Git verification failed")
    return result.stdout.strip()


def _clean_git_head_matches(checkout, expected_sha):
    """Require exact source identity and no modified or untracked code."""
    if not isinstance(expected_sha, str) or not SHA.fullmatch(expected_sha):
        raise ValueError("unverified expected source SHA")
    path = Path(checkout)
    if not path.is_dir() or path.is_symlink():
        raise ValueError("local dependency source is not a direct directory")
    # git -C accepts nested directories and returns the parent repository's
    # HEAD; importing from an arbitrary subtree would silently change scope.
    toplevel = _run_git(path, "rev-parse", "--show-toplevel")
    if Path(toplevel).resolve() != path.resolve():
        raise ValueError("dependency checkout must be repository root")
    if _run_git(path, "rev-parse", "--verify", "HEAD") != expected_sha:
        raise ValueError("local dependency source does not match pinned head")
    if _run_git(path, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("dependency checkout has unreviewed changes")
    # Git status hides ignored files, but Python imports do not. An ignored
    # shadow module could execute despite a matching HEAD and clean status.
    if _run_git(path, "ls-files", "--others", "--ignored", "--exclude-standard"):
        raise ValueError("dependency checkout contains ignored unreviewed content")
    # Tracked links and gitlinks can redirect imports outside the pinned tree
    # or introduce an independently versioned submodule.
    for entry in _run_git(path, "ls-files", "--stage").splitlines():
        if entry.startswith(("120000 ", "160000 ")):
            raise ValueError("dependency source contains linked content")
    return True


def verify_local_checkout(checkout, repo):
    """Verify exact approved commit without fetching, installing or executing code."""
    binding = resolve_repo(repo)
    if repo == "thebrazenbeard/orgasm":
        raise ValueError("historical alias cannot activate a second engine")
    # A matching commit alone does not establish which canonical source
    # checkout was supplied. This is a provenance sanity check, not proof
    # against a malicious local administrator who can rewrite Git config.
    expected = f"https://github.com/{repo}.git"
    origin = _run_git(checkout, "remote", "get-url", "origin")
    if origin != expected:
        raise ValueError("dependency checkout origin is not canonical")
    return _clean_git_head_matches(checkout, binding["sha"])
