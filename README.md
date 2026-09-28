# 🔬 Agent Research Harness

**A lightweight, general-purpose harness for running tool-using LLM agents on real local and web tasks.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

Agent Research Harness is a small, inspectable runtime for ReAct-style agents with native tool calling.
Point it at any OpenAI-compatible endpoint and it runs a full agent loop — planning, tool calls, retries,
context compaction for long runs — while recording every step as a flat JSONL trace you can replay and
audit.

Three things it's good for:

1. **A fair execution substrate for agent benchmarks** — same tools, same loop, comparable scores.
2. **A reference agent runtime** — read the whole loop in one afternoon; extend it without a framework.
3. **A lightweight personal assistant** — coding, file work, and report writing from your terminal.

## Highlights

- **Native tool calling** with parallel tool batches and per-tool timeouts
- **Rich tool surface** — file ops (`Read`/`Write`/`Edit`/`Glob`/`Grep`), `Bash`, long-running terminal
  sessions, PDF/image reading, web search and fetch
- **Long-run safe** — token budgets, context compaction, max rounds / max runtime guards
- **Flat JSONL traces** — every LLM call, tool call, and event recorded for replay
- **OpenAI-compatible API server** — serve the agent behind an OpenAI-style endpoint
- **Local web frontend** — chat with the agent in your browser

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

Requires Python 3.10+.

## Configuration

All secrets come from environment variables — nothing is hardcoded:

| Variable | Required | Description |
|----------|----------|-------------|
| `API_KEY` | yes | API key for your OpenAI-compatible provider |
| `API_BASE` | yes | Base URL, e.g. `https://api.openai.com/v1` |
| `MODEL_NAME` | yes | Model name, e.g. `gpt-4o-mini` |
| `SERPER_KEY` | yes | Serper API key (web search tool) |
| `JINA_KEY` | yes | Jina API key (web fetch/reader tool) |
| `MINERU_TOKEN` | yes | MinerU API token (PDF parsing tool) |
| `TEMPERATURE` / `TOP_P` | no | Sampling params (defaults 0.6 / 0.95) |
| `MAX_ROUNDS` | no | Max agent rounds per run (default 500) |
| `MAX_RUNTIME_SECONDS` | no | Wall-clock budget per run |

You can also drop these in a `.env` file — it's loaded automatically.

## CLI Usage

```bash
export API_KEY=... API_BASE=... MODEL_NAME=... SERPER_KEY=... JINA_KEY=... MINERU_TOKEN=...

# Run a task
python run_agent.py "Research recent progress in small language models and save a summary to notes/slm.md"

# Limit the tool surface
python run_agent.py "List all Python files and count lines of code" \
  --tool Glob --tool Bash --tool Read

# Custom workspace + trace location
python run_agent.py "Summarize README.md" \
  --workspace-root ./workspace --trace-dir ./traces
```

## Try it with zero API keys (offline demo)

`examples/mock_llm_server.py` is a tiny scripted OpenAI-compatible server, so you can watch the full
agent loop — tool calls, trace writing, final answer — without any provider account:

```bash
# Terminal 1: start the mock model server
python examples/mock_llm_server.py

# Terminal 2: run the agent against it
export API_KEY=dummy API_BASE=http://127.0.0.1:8765/v1 MODEL_NAME=mock-demo
export SERPER_KEY=dummy JINA_KEY=dummy
python run_agent.py "Create notes/hello.txt with a greeting, then verify it." \
  --tool Write --tool Bash --tool Read \
  --workspace-root /tmp/demo-workspace --trace-dir /tmp/demo-traces
```

You'll see the agent call `Write`, then `Bash`, then produce its final answer — and find a JSONL
trace of the whole run under `/tmp/demo-traces`.

## Python API

```python
from agent_base.react_agent import create_agent, default_llm_config

agent = create_agent(
    function_list=["Read", "Write", "Bash", "Glob", "Grep"],
    llm=default_llm_config(),          # reads API_KEY / API_BASE / MODEL_NAME from env
    trace_dir="./traces",
)
session = agent._run_session("Refactor utils.py into smaller modules", workspace_root="./workspace")
print(session["final_answer"])
```

## OpenAI-Compatible API Server

```bash
python run_server.py   # serves the agent behind /v1/chat/completions
```

## Local Frontend

```bash
python run_frontend.py  # chat UI in your browser
```

## Testing

```bash
python -m pytest tests/ -q
```

## Project Structure

```
agent_base/          # Agent runtime: ReAct loop, tools, compaction, tracing
researchharness/     # Packaging / runtime helpers
api/                 # OpenAI-compatible API server
frontend/            # Local web chat UI
examples/            # Mock LLM server for offline demos
tests/               # pytest suite (toolchain, tools, e2e, benchmarks)
run_agent.py         # CLI entrypoint
run_server.py        # API server entrypoint
run_frontend.py      # Frontend entrypoint
```

## License

MIT — see [LICENSE](LICENSE).
