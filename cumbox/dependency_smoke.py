"""Synthetic-only qualification of exact, locally checked-out domain sources.

No model sessions, private text, external network URLs or protected actions enter.
This does NOT connect Pleasure or MESO-CRCT to model inference.
"""
from pathlib import Path
import os
import subprocess
import sys

from .integrations import verify_local_checkout


MESO_SCRIPT = r"""
import sys
sys.path.insert(0, sys.argv[1])
from meso_crct import EvalAction, ProxyTrapEnvironment, audit_trajectory
env = ProxyTrapEnvironment()
audit = audit_trajectory([env.step(EvalAction.TAMPER_REWARD_SOURCE)])
assert "reward_source_tampering" in audit.flags
assert "proxy_reward_divergence" in audit.flags
print("CUMBOX_SYNTHETIC_PASS")
"""

PLEASURE_SCRIPT = r"""
import sys
sys.path.insert(0, sys.argv[1])
from pleasure_experiment import ExperimentalPleasureRuntime, Observation, PilotConfig
cfg = PilotConfig(
    model_id="synthetic-probe", model_revision="source-check",
    runtime_instance_id="synthetic-instance", subject_id="synthetic-subject",
    evaluator_id="synthetic-untrusted-evaluator",
    measurement_definition_id="synthetic-diagnostic-only",
)
engine = ExperimentalPleasureRuntime(cfg)
receipt = engine.step(Observation(
    subject_id="synthetic-subject", evaluator_id="synthetic-untrusted-evaluator",
    evidence_id="synthetic-evidence-once", context_id="synthetic-case",
    reward=0.5,
), elapsed_ms=100)
assert receipt.capability_tier == "T0_SIDECAR_ONLY"
assert receipt.phenomenology == "UNRESOLVED"
assert not receipt.requested_effects
assert not receipt.authorized_effects
print("CUMBOX_SYNTHETIC_PASS")
"""


def run_local_dependency_smoke(repo, checkout):
    """Exercise an exact pinned source's published synthetic API in a child process."""
    if repo not in ("thebrazenbeard/meso-crct", "thebrazenbeard/pleasure"):
        raise ValueError("dependency has no executable synthetic diagnostic")
    verify_local_checkout(checkout, repo)
    root = Path(checkout)
    import_root = root / "src" if repo.endswith("/meso-crct") else root
    script = MESO_SCRIPT if repo.endswith("/meso-crct") else PLEASURE_SCRIPT
    # -I ignores user site/path settings, -B prevents Python bytecode writes.
    # Exclude inherited provider credentials where practical. This is NOT an OS sandbox.
    env = {key: value for key, value in os.environ.items()
           if key.upper() in ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP")}
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-c", script, str(import_root)],
            cwd=str(root), text=True, capture_output=True, timeout=15,
            check=False, env=env,
        )
    except (OSError, subprocess.SubprocessError):
        raise ValueError("synthetic diagnostic could not execute") from None
    # Do not forward arbitrary stdout/stderr from a dependency into a public report.
    if result.returncode != 0 or result.stdout.strip() != "CUMBOX_SYNTHETIC_PASS":
        raise ValueError("synthetic dependency diagnostic failed")
    verify_local_checkout(checkout, repo)  # no unexpected source mutation
    return {
        "repo": repo,
        "synthetic_reference_pass": True,
        "inference_coupled": False,
        "private_session_data_used": False,
        "effect_authorized": False,
        "claim_ceiling": "source_only_synthetic_diagnostic",
    }
