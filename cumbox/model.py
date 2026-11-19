"""Ollama chat adapter constrained to literal loopback HTTP only."""
import ipaddress
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .session import DECISION_JSON_SCHEMA


MODEL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,119}$")
MAX_REPLY_BYTES = 131072


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_endpoint(url):
    """Reject remote destinations, hostname resolution, credentials and redirects."""
    if not isinstance(url, str):
        raise ValueError("invalid model endpoint")
    try:
        parsed = urlsplit(url)
        ip = ipaddress.ip_address(parsed.hostname or "")
        port = parsed.port
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid model endpoint") from None
    if (parsed.scheme != "http" or not ip.is_loopback or
            not port or parsed.path != "/api/chat" or
            parsed.query or parsed.fragment or
            parsed.username is not None or parsed.password is not None):
        raise ValueError("model endpoint must be literal loopback /api/chat")
    return url


class LocalOllama:
    """Only session-scoped local POSTs; does not persist or print responses."""

    def __init__(self, model, *, endpoint="http://127.0.0.1:11434/api/chat",
                 timeout_seconds=25, think=None):
        if (not isinstance(model, str) or not MODEL_NAME.fullmatch(model) or
                ".." in model or "//" in model):
            raise ValueError("invalid model name")
        if (type(timeout_seconds) not in (int, float) or
                not 0.1 <= timeout_seconds <= 30):
            raise ValueError("invalid local timeout")
        if think is not None and type(think) is not bool:
            raise ValueError("thinking override must be boolean or omitted")
        self.think = think
        self.model = model
        self.endpoint = validate_endpoint(endpoint)
        self.timeout_seconds = timeout_seconds

    def generate(self, messages):
        payload = {"model": self.model, "messages": messages,
                   "format": DECISION_JSON_SCHEMA, "stream": False,
                   "options": {"num_predict": 512, "temperature": 0.75}}
        if self.think is not None:
            payload["think"] = self.think
        request = Request(
            self.endpoint,
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        opener = build_opener(ProxyHandler({}), NoRedirect())
        try:
            with opener.open(request, timeout=self.timeout_seconds) as response:
                raw = response.read(MAX_REPLY_BYTES + 1)
        except (HTTPError, URLError, OSError, TimeoutError, ValueError) as exc:
            if isinstance(exc, HTTPError):
                exc.close()
            raise RuntimeError("local model call failed") from None
        if len(raw) > MAX_REPLY_BYTES:
            raise RuntimeError("local model reply oversized")
        def reject_duplicate_fields(pairs):
            obj = {}
            for key, value in pairs:
                if key in obj:
                    raise ValueError("duplicate envelope field")
                obj[key] = value
            return obj

        try:
            obj = json.loads(raw, object_pairs_hook=reject_duplicate_fields,
                             parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            if (not isinstance(obj, dict) or obj.get("done") is not True or
                    "error" in obj):
                raise ValueError("invalid envelope")
            message = obj["message"]
            if (not isinstance(message, dict) or
                    message.get("role") != "assistant" or
                    "tool_calls" in message):
                raise ValueError("invalid message")
            answer = message["content"]
        except (ValueError, KeyError, TypeError, UnicodeDecodeError, RecursionError):
            raise RuntimeError("local model response invalid") from None
        if not isinstance(answer, str):
            raise RuntimeError("local model response invalid")
        return answer
