#!/usr/bin/env python3
"""Mock OpenAI-compatible LLM server for offline demos and smoke tests.

Serves a *scripted* multi-turn tool-calling sequence at
``POST /v1/chat/completions`` so the agent harness can be exercised end to
end without any API key or network access to a real provider.

The script below demonstrates the core loop:
    turn 1 -> Write a file with the Write tool
    turn 2 -> verify it with the Bash tool
    turn 3 -> final answer (no tool calls)

Run:
    python examples/mock_llm_server.py [--port 8765]

Then in another terminal:
    export API_KEY=dummy API_BASE=http://127.0.0.1:8765/v1 MODEL_NAME=mock-demo
    export SERPER_KEY=dummy JINA_KEY=dummy
    python run_agent.py "Create notes/hello.txt with a greeting, then verify it." \\
        --tool Write --tool Bash --tool Read \\
        --workspace-root /tmp/demo-workspace --trace-dir /tmp/demo-traces
"""

from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SCRIPT = [
    {
        "role": "assistant",
        "content": "I'll create the file first.",
        "tool_calls": [
            {
                "id": "call_write_1",
                "type": "function",
                "function": {
                    "name": "Write",
                    "arguments": json.dumps(
                        {
                            "path": "notes/hello.txt",
                            "content": (
                                "Hello from the agent harness demo!\n"
                                "This file was written by an LLM agent running\n"
                                "against a local mock model server.\n"
                            ),
                            "overwrite": True,
                        }
                    ),
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": "File written. Now let me verify it with Bash.",
        "tool_calls": [
            {
                "id": "call_bash_1",
                "type": "function",
                "function": {
                    "name": "Bash",
                    "arguments": json.dumps({"command": "cat notes/hello.txt"}),
                },
            }
        ],
    },
    {
        "role": "assistant",
        "content": (
            "Done. I created `notes/hello.txt` with a greeting using the Write tool, "
            "then verified its contents with the Bash tool (`cat notes/hello.txt`). "
            "The file exists in the workspace and contains the expected greeting."
        ),
    },
]


class Handler(BaseHTTPRequestHandler):
    turn = 0

    def log_message(self, *args):  # keep demo output clean
        pass

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            self._send_json({"data": [{"id": "mock-demo", "object": "model"}]})
        else:
            self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            self.rfile.read(length)
        if not self.path.rstrip("/").endswith("/chat/completions"):
            self._send_json({"error": "not found"}, status=404)
            return
        idx = min(Handler.turn, len(SCRIPT) - 1)
        Handler.turn += 1
        step = SCRIPT[idx]
        message = {"role": "assistant", "content": step.get("content")}
        finish = "stop"
        if step.get("tool_calls"):
            message["tool_calls"] = step["tool_calls"]
            finish = "tool_calls"
        self._send_json(
            {
                "id": f"chatcmpl-mock-{int(time.time())}-{idx}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "mock-demo",
                "choices": [
                    {
                        "index": 0,
                        "message": message,
                        "finish_reason": finish,
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            }
        )


def main():
    parser = argparse.ArgumentParser(description="Mock OpenAI-compatible LLM server.")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"mock llm server on http://127.0.0.1:{args.port}/v1")
    server.serve_forever()


if __name__ == "__main__":
    main()
