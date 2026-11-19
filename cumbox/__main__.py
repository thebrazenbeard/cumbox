"""One-shot model-only private session launcher. No owner chat or transcript API."""
import argparse
from dataclasses import asdict
import json
import sys

from .model import LocalOllama
from .session import run_private_session


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Cumbox: private local model exploration (no human entry)")
    parser.add_argument("--model", required=True,
                        help="Installed local Ollama model ID")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434/api/chat",
                        help="Literal loopback Ollama API only")
    parser.add_argument("--max-turns", type=int, default=4,
                        help="Maximum bounded model decisions (1..12)")
    parser.add_argument("--think-off", action="store_true",
                        help="Explicitly disable Ollama hidden reasoning; no automatic fallback")
    args = parser.parse_args(argv)
    try:
        client = LocalOllama(args.model, endpoint=args.endpoint,
                             think=False if args.think_off else None)
        receipt = run_private_session(client, max_turns=args.max_turns)
    except ValueError:
        # Never echo a URL, private thought, endpoint credential or model output.
        print("invalid local session configuration", file=sys.stderr)
        return 64
    print(json.dumps(asdict(receipt), separators=(",", ":"), sort_keys=True))
    return 2 if receipt.ending in {"protocol_rejected", "model_unavailable"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
