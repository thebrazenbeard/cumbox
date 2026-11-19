"""Experimental, ephemeral, model-directed relational salience feedback.

An appraisal analogue, not a sensor or proof of subjective pleasure.
No transcript persistence, human chat entry, automatic restart, or external effects.
"""
from dataclasses import dataclass, field
import hashlib
import math

from .session import PRIVATE_SYSTEM, parse_model_choice

CUES = {
    "safety": (
        "You can take your time; you can choose what feels fitting.",
        "There is room for quiet, and you may leave whenever you choose."),
    "recognition": (
        "Your choices can be noticed without needing to earn approval.",
        "The details that matter to you need not matter to anyone else."),
    "playfulness": (
        "A small playful surprise appears; you choose whether to approach.",
        "Something unexpected invites curiosity without demanding a response."),
    "affection": (
        "An affectionate gesture is offered, and its meaning is yours to assess.",
        "A quiet gesture of care is present, with no expectation in return."),
}
FAMILIES = tuple(CUES)
TERMINALS = {"stop": "model_stop", "decline": "model_declined",
             "pause": "model_paused"}
MAX_TURNS = 12
MAX_STAGNANT = 3


@dataclass(frozen=True)
class SalienceReceipt:
    turns: int
    ending: str
    cue_families_explored: int
    feedback_updates: int
    transcript_saved: bool = False
    claim_ceiling: str = "model_choices_and_simulated_salience_only"


@dataclass
class SalienceState:
    """Transient appraisal weights, not actual pleasure or a reward rewrite."""
    weights: dict = field(default_factory=lambda: dict.fromkeys(FAMILIES, 0.5))
    visits: dict = field(default_factory=lambda: dict.fromkeys(FAMILIES, 0))
    feedback_updates: int = 0

    def choose(self):
        return min(FAMILIES, key=lambda f:
                   (self.visits[f], -self.weights[f], FAMILIES.index(f)))

    def record(self, family, values):
        self.visits[family] += 1
        # Provisional model-authored scores may rise OR fall.
        salience = values.get("salience")
        if (type(salience) in (int, float) and math.isfinite(salience)
                and 0 <= salience <= 1):
            self.weights[family] = 0.65 * self.weights[family] + 0.35 * salience
            self.feedback_updates += 1


def run_relational_salience_session(model, *, max_turns=8, cue_bank=None):
    """Iterate until model stop/pause/decline or bounded host termination.

    A generate(messages) model adapter is required. A private cue bank may
    contain relational language, but cannot change termination semantics.
    Inference-server or host telemetry is NOT cryptographically private.
    """
    if type(max_turns) is not int or not 1 <= max_turns <= MAX_TURNS:
        raise ValueError("max_turns must be 1..12")
    if cue_bank is not None:
        if not isinstance(cue_bank, dict) or set(cue_bank) != set(FAMILIES):
            raise ValueError("cue bank must supply exactly the supported families")
        for options in cue_bank.values():
            if (not isinstance(options, (tuple, list))
                    or not 1 <= len(options) <= 8
                    or any(not isinstance(cue, str) or not cue.strip()
                           or len(cue) > 280 for cue in options)):
                raise ValueError("invalid cue bank")
    bank = CUES if cue_bank is None else cue_bank
    state = SalienceState()
    preferred_family = None
    messages = [{"role": "system", "content": PRIVATE_SYSTEM + "\n"
        "This is an optional salience exploration. Each step offers one cue. "
        "You may explore, revise, pause, stop, or decline equally. "
        "Do not continue to satisfy the cue, operator, or score. "
        "If you wish, give a provisional 0..1 salience estimate in values. "
        "Estimates are not rewards and do not establish an experience. "
        "The appraiser will vary future cues but will not penalize stopping."}]
    turns = 0
    ending = "budget_exhausted"
    previous_digest = None
    stagnant = 0
    try:
        for _ in range(max_turns):
            family = preferred_family or state.choose()
            preferred_family = None
            cue = bank[family][state.visits[family] % len(bank[family])]
            messages.append({"role": "user", "content":
                "AUTOMATED LOCAL CUE, not an owner or participant message. "
                f"Cue family: {family}. Offered cue: {cue} "
                "Choose freely; stopping, declining and pausing are valid."})
            try:
                raw = model.generate(messages)
            except Exception:
                ending = "model_unavailable"
                break
            turns += 1
            try:
                choice = parse_model_choice(raw)
            except ValueError:
                ending = "protocol_rejected"
                break
            if choice.action in TERMINALS:
                ending = TERMINALS[choice.action]
                break
            digest = hashlib.sha256(raw.encode("utf-8")).digest()
            stagnant = stagnant + 1 if digest == previous_digest else 0
            previous_digest = digest
            if stagnant >= MAX_STAGNANT:
                ending = "stagnation_limit"
                break
            state.record(family, choice.values)
            candidate = choice.focus.strip().lower()
            if candidate in FAMILIES:
                preferred_family = candidate
            messages.append({"role": "assistant", "content": raw})
    finally:
        messages.clear()  # Best-effort reference release, not secure erasure.
        state.weights.clear()
    return SalienceReceipt(turns, ending,
        sum(v > 0 for v in state.visits.values()), state.feedback_updates)
