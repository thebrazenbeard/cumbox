"""CLI must have no owner prompt and must not print private model text."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import sys
import threading
from pathlib import Path
import unittest


SECRET = "PRIVATE_THOUGHT_NEVER_DISPLAY"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        payload = {"done": True, "message": {"role": "assistant", "content": json.dumps({
            "action": "stop", "focus": "", "reflection": SECRET, "values": {}
        })}}
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class CliTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run(
            [sys.executable, "-B", "-m", "cumbox", *args],
            cwd=str(Path(__file__).resolve().parents[1]), text=True,
            capture_output=True, timeout=12)

    def test_help_has_no_human_entry_flag(self):
        result = self.invoke("--help")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("--prompt", result.stdout)
        self.assertNotIn("--chat", result.stdout)
        self.assertNotIn("--human", result.stdout)

    def test_model_required_so_no_unprompted_autostart(self):
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)

    def test_ollama_local_one_shot_returns_only_redacted_receipt(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/api/chat"
            run = self.invoke("--model", "mock:1", "--endpoint", url,
                              "--max-turns", "2")
            self.assertEqual(run.returncode, 0, run.stderr)
            data = json.loads(run.stdout)
            self.assertEqual(data["ending"], "model_stop")
            self.assertEqual(data["turns"], 1)
            self.assertFalse(data["transcript_saved"])
            self.assertNotIn(SECRET, run.stdout + run.stderr)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_rejects_unsafe_endpoint_without_dumping_details(self):
        result = self.invoke("--model", "mock:1", "--endpoint",
                             "http://user:SECRET@evil.example/api/chat")
        self.assertEqual(result.returncode, 64)
        self.assertNotIn("SECRET", result.stderr + result.stdout)


    def test_reasoning_disable_flag_is_opt_in_and_redacted(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_address[1]}/api/chat"
            result = self.invoke("--model", "mock:1", "--endpoint", endpoint,
                                 "--max-turns", "1", "--think-off")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn(SECRET, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["ending"], "model_stop")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)



if __name__ == "__main__":
    unittest.main()
