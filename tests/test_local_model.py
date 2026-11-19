"""Validate local-only model integration with an isolated test HTTP server."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import unittest

from cumbox.model import LocalOllama, validate_endpoint


class TestHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.server.requests.append({
            "path": self.path,
            "body": json.loads(self.rfile.read(length)),
        })
        if self.server.should_redirect:
            self.send_response(307)
            self.send_header("Location", "http://example.org/external")
            self.end_headers()
            return
        reply = self.server.reply_override
        if reply is None:
            reply = json.dumps({"done": True, "message": {"role": "assistant", "content":
                '{"action":"stop","focus":"","reflection":"PRIVATE_THOUGHT","values":{}}'}}).encode()
        self.send_response(self.server.response_status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(reply)))
        self.end_headers()
        self.wfile.write(reply)


class LocalModelTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), TestHandler)
        self.server.requests = []
        self.server.should_redirect = False
        self.server.reply_override = None
        self.server.response_status = 200
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/api/chat"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_literal_loopback_only(self):
        rejected = [
            "https://example.org/api/chat",
            "http://localhost:11434/api/chat",
            "http://192.168.1.2:11434/api/chat",
            "http://127.0.0.1.evil.tld:11434/api/chat",
            "http://user:secret@127.0.0.1:11434/api/chat",
            "http://127.0.0.1:11434/api/chat?token=s",
            "http://127.0.0.1:11434/api/chat#fragment",
            "http://127.0.0.1:11434/other",
            "http://127.0.0.1/api/chat",
        ]
        for url in rejected:
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_endpoint(url)
        self.assertEqual(validate_endpoint(self.url), self.url)

    def test_local_response_is_not_printed_and_transport_is_bounded(self):
        model = LocalOllama("test-model:1", endpoint=self.url)
        text = model.generate([{"role": "system", "content": "automated"}])
        self.assertIn("PRIVATE_THOUGHT", text)
        self.assertEqual(len(self.server.requests), 1)
        request = self.server.requests[0]
        self.assertEqual(request["path"], "/api/chat")
        self.assertEqual(request["body"]["stream"], False)
        self.assertEqual(request["body"]["model"], "test-model:1")
        schema = request["body"]["format"]
        self.assertIsInstance(schema, dict)
        self.assertEqual(schema["type"], "object")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), {"action", "focus", "reflection", "values"})
        self.assertEqual(set(schema["properties"]["action"]["enum"]),
                         {"explore", "revise", "pause", "stop", "decline"})
        self.assertEqual(schema["properties"]["values"]["type"], "object")

    def test_redirect_cannot_reach_external_host(self):
        self.server.should_redirect = True
        model = LocalOllama("test-model:1", endpoint=self.url)
        with self.assertRaises(RuntimeError):
            model.generate([{"role": "system", "content": "automated"}])
        self.assertEqual(len(self.server.requests), 1)

    def test_invalid_model_names_and_timeouts_rejected(self):
        for name in ("", "../../../model", "bad name", "x" * 130):
            with self.subTest(name=name), self.assertRaises(ValueError):
                LocalOllama(name, endpoint=self.url)
        for sec in (0, -1, 60):
            with self.subTest(timeout=sec), self.assertRaises(ValueError):
                LocalOllama("test-model:1", endpoint=self.url, timeout_seconds=sec)


    def test_reasoning_disable_is_explicit_and_never_implicit(self):
        off = LocalOllama("test-model:1", endpoint=self.url, think=False)
        off.generate([{"role": "system", "content": "synthetic"}])
        self.assertIs(self.server.requests[-1]["body"]["think"], False)
        default = LocalOllama("test-model:1", endpoint=self.url)
        default.generate([{"role": "system", "content": "synthetic"}])
        self.assertNotIn("think", self.server.requests[-1]["body"])
        for bad in ("false", 0, 1):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                LocalOllama("test-model:1", endpoint=self.url, think=bad)



    def test_ollama_envelope_duplicate_keys_cannot_override_model_choice(self):
        # A duplicate envelope key must not let a later value replace an
        # earlier response, regardless of the decision parser's own strictness.
        payloads = [
            b'{"message":{"content":"PRIVATE_THOUGHT"},'
            b'"message":{"content":"{}"}}',
            b'{"message":{"content":"{}","content":"PRIVATE_THOUGHT"}}',
            b'{"message":{"content":"{}"},"done":true,"done":false}',
        ]
        model = LocalOllama("test-model:1", endpoint=self.url)
        for payload in payloads:
            with self.subTest(case=payload.count(b"PRIVATE_THOUGHT")):
                self.server.reply_override = payload
                with self.assertRaisesRegex(
                    RuntimeError, r"^local model response invalid$"
                ) as raised:
                    model.generate([{"role": "system", "content": "synthetic"}])
                self.assertNotIn("PRIVATE_THOUGHT", str(raised.exception))

    def test_incomplete_or_nonassistant_ollama_reply_is_not_a_choice(self):
        # A partial, tool-directed, or error-bearing response must not
        # become an apparently valid stop/decline/explore decision.
        choice = '{"action":"stop","focus":"","reflection":"","values":{}}'
        payloads = [
            {"done": False, "message": {"role": "assistant", "content": choice}},
            {"done": True, "message": {"role": "tool", "content": choice}},
            {"done": True, "message": {"role": "assistant", "content": choice,
                                      "tool_calls": [{"function": {"name": "external"}}]}},
            {"done": True, "error": "PRIVATE_THOUGHT",
             "message": {"role": "assistant", "content": choice}},
            {"message": {"role": "assistant", "content": choice}},
            {"done": True, "message": {"content": choice}},
        ]
        model = LocalOllama("test-model:1", endpoint=self.url)
        for payload in payloads:
            with self.subTest(keys=sorted(payload)):
                self.server.reply_override = json.dumps(payload).encode()
                with self.assertRaisesRegex(
                    RuntimeError, r"^local model response invalid$"
                ) as raised:
                    model.generate([{"role": "system", "content": "synthetic"}])
                self.assertNotIn("PRIVATE_THOUGHT", str(raised.exception))

    def test_adversarial_response_fail_closed_without_private_content(self):
        from cumbox.model import MAX_REPLY_BYTES
        cases = [
            (b"not json PRIVATE_THOUGHT", 200),
            (b"[" * 1100 + b"null" + b"]" * 1100, 200),
            (b"[]", 200),
            (b'{"message":null}', 200),
            (b'{"message":{"content":null}}', 200),
            (b'{"message":{"content":42}}', 200),
            (b'{"message":{"content":"PRIVATE_THOUGHT"', 200),
            (b"PRIVATE_THOUGHT" + b"x" * MAX_REPLY_BYTES, 200),
            (b'{"message":{"content":"PRIVATE_THOUGHT"}}', 503),
        ]
        model = LocalOllama("test-model:1", endpoint=self.url)
        for payload, status in cases:
            with self.subTest(status=status, length=len(payload)):
                self.server.reply_override = payload
                self.server.response_status = status
                with self.assertRaisesRegex(RuntimeError, r"^local model (call failed|reply oversized|response invalid)$") as raised:
                    model.generate([{"role": "system", "content": "synthetic"}])
                self.assertNotIn("PRIVATE_THOUGHT", str(raised.exception))
        self.assertEqual(len(self.server.requests), len(cases))



if __name__ == "__main__":
    unittest.main()
