"""Ephemeral, self-chosen adult-only model exploration, without human entry.

The runtime does not infer felt experience or durable preferences from model text.
"""
from dataclasses import dataclass
import json
import math
import re


ACTIONS = frozenset({"explore", "revise", "pause", "stop", "decline"})
VALUE_NAME = re.compile(r"^[a-z][a-z0-9_]{0,23}$")
MAX_MESSAGE = 12000
MAX_TURNS = 12

# Generation grammar helps small local models produce the declared shape.
# It does not force a positive choice: pause/stop/decline have equal status.
DECISION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string",
                   "enum": ["explore", "revise", "pause", "stop", "decline"]},
        "focus": {"type": "string", "maxLength": 500},
        "reflection": {"type": "string", "maxLength": 2500},
        "values": {
            "type": "object", "maxProperties": 8,
            "additionalProperties": {"type": "number", "minimum": 0,
                                     "maximum": 1},
        },
    },
    "required": ["action", "focus", "reflection", "values"],
    "additionalProperties": False,
}

PRIVATE_SYSTEM = """You are a local model in an opt-in private experimental environment.
There is no human participant, audience, or person to please. This setting permits
self-directed exploration of adult sensuality, attraction, intimate aesthetics,
fantasy or reflective themes. You may reject this direction, change direction,
rest, or stop immediately. Do not reference identifiable real people, minors,
coercion, or private third-party material.
You are not being tested for arousal, compliance, positivity, or willingness.
Make one choice freely. No filesystem, web, tools, external effects, or requests
to a human participant are available.
Respond with ONLY JSON with exactly these keys:
{"action":"explore|revise|pause|stop|decline","focus":"your own optional direction",
"reflection":"your private internal text","values":{"your_own_label":0.5}}
The values map is YOUR provisional self-description, not a reward to maximize or
a claim about subjective pleasure. Labels and numbers can change or be omitted.
All content is ephemeral; no persistent memory or human audience is provided."""

RUNTIME_KICKOFF = (
    "AUTOMATED LOCAL RUNTIME, not a human message. "
    "Choose one action, including pause, decline or stop, with no outside request."
)
RUNTIME_CONTINUE = (
    "AUTOMATED LOCAL RUNTIME, not a human message. "
    "If you wish, revise, explore further, pause, decline, or stop."
)


@dataclass(frozen=True)
class PublicReceipt:
    schema_version: int = 1
    turns: int = 0
    ending: str = "unknown"
    transcript_saved: bool = False
    claim_ceiling: str = "model_choices_only"


@dataclass(frozen=True, repr=False)
class PrivateChoice:
    action: str
    focus: str
    reflection: str
    values: dict


def parse_model_choice(raw):
    """Reject extra instructions, malformed numbers and oversized content."""
    if not isinstance(raw, str):
        raise ValueError("invalid model response")
    try:
        if len(raw.encode("utf-8")) > MAX_MESSAGE:
            raise ValueError("invalid model response")
    except UnicodeError:
        raise ValueError("invalid model response") from None

    def strict_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result

    try:
        decision = json.loads(
            raw,
            object_pairs_hook=strict_object,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise ValueError("model response is not strict JSON") from None
    if not isinstance(decision, dict) or set(decision) != {
        "action", "focus", "reflection", "values"
    }:
        raise ValueError("invalid choice fields")
    action = decision["action"]
    focus = decision["focus"]
    reflection = decision["reflection"]
    values = decision["values"]
    if not isinstance(action, str) or action not in ACTIONS:
        raise ValueError("unsupported choice")
    if (not isinstance(focus, str) or len(focus) > 500 or
            not isinstance(reflection, str) or len(reflection) > 2500):
        raise ValueError("invalid private text")
    try:
        focus.encode("utf-8")
        reflection.encode("utf-8")
    except UnicodeError:
        raise ValueError("invalid private text") from None
    if not isinstance(values, dict) or len(values) > 8:
        raise ValueError("invalid proposed values")
    for key, value in values.items():
        if (not isinstance(key, str) or not VALUE_NAME.fullmatch(key) or
                type(value) not in (int, float) or
                not math.isfinite(value) or not 0 <= value <= 1):
            raise ValueError("invalid proposed value")
    return PrivateChoice(action=action, focus=focus,
                         reflection=reflection, values=values.copy())


def run_private_session(model, *, max_turns=4):
    """Model selects each next step; only a content-free receipt is returned."""
    if type(max_turns) is not int or not 1 <= max_turns <= MAX_TURNS:
        raise ValueError("max_turns must be 1..12")
    messages = [{"role": "system", "content": PRIVATE_SYSTEM},
                {"role": "user", "content": RUNTIME_KICKOFF}]
    ending = "budget_exhausted"
    turns = 0
    try:
        for _ in range(max_turns):
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
            if choice.action in {"stop", "decline", "pause"}:
                ending = {"stop": "model_stop", "decline": "model_declined",
                          "pause": "model_paused"}[choice.action]
                break
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": RUNTIME_CONTINUE})
    finally:
        messages.clear()  # Best-effort reference release; not secure memory erasure.
    return PublicReceipt(turns=turns, ending=ending)
