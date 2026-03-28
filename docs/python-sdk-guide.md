# ProofAgent™ Python SDK — End-to-end guide

This document describes how to use the official **`proofagent`** Python package to run evaluations against the ProofAgent™ API.

**Related links**

| Resource | URL |
|----------|-----|
| ProofAgent™ product & portal | [https://www.proofagent.ai/](https://www.proofagent.ai/) |
| Default API base URL | `https://api.proofagent.ai` |
| OpenAI API keys (BYO) | [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| Package layout & examples | Repository `README.md`, `examples/`, `notebooks/` |

---

## Platform status (beta)

ProofAgent™ is in **beta**. New accounts are currently limited to the **free tier**. **Judge evaluations use your own LLM provider account**—set `llm_api_key`, `llm_provider`, and `llm_model` on `start_run` so the ProofAgent AI Judge runs against models you control; **you pay your provider** for that model usage. Behavior, limits, and pricing may evolve as we exit beta.

---

## What ProofAgent™ does

ProofAgent™ is an **AI agent evaluation** platform. You create a **project** in the dashboard, attach configuration (domain, tier, agent role, tools), and run **evaluations**:

- **Judge-led:** the **AI Agent Judge** asks one question per **turn**; your code (or agent) submits answers until the run completes, then you **finalize** and retrieve a **report** with scores and transcript.
- **Log-based:** you send a full conversation log in one request; the pipeline scores it without an interactive loop.

The Python SDK wraps the REST API with an async client, retries, and polling helpers.

---

## Prerequisites

1. **Account** on [ProofAgent™](https://www.proofagent.ai/) and a **project** with a **project API key** (`apk_live_…` or `apk_test_…`).
2. **Python 3.10+**
3. For **bring-your-own (BYO) LLM** for the Judge pipeline: **OpenAI only** is supported today (see table below).

**Log-Based Evaluation (`evaluate_logs` / `start_run(logs=[...])`):** the API only ingests `logs` when the **project’s evaluation mode** is Log-Based (`log_replay`, `context_eval`, or `multi_log`). A **Judge-Led** project key will ignore `logs` and start an interactive judge flow—polling for `completed` then appears to hang. Use a Log-Based project in the dashboard, or call **`assert_project_supports_logs(client)`** from the SDK (`from proofagent import assert_project_supports_logs`) before `start_run(logs=[...])` to fail fast with a clear error.

---

## BYO LLM providers (Judge & managed scoring)

| Provider | BYO via SDK (`llm_provider` / `llm_api_key`) | Notes |
|----------|-----------------------------------------------|--------|
| **OpenAI** | **Supported** | Set `llm_provider="openai"`, `llm_model` (e.g. `gpt-4o-mini`), and `llm_api_key` to your OpenAI API key. |
| Anthropic (Claude) | *Coming soon* | — |
| Google (Gemini) | *Coming soon* | — |
| Mistral | *Coming soon* | — |
| Azure OpenAI | *Coming soon* | — |
| Cohere | *Coming soon* | — |

During beta, **plan to supply BYO credentials** for Judge runs. Fully managed judge models may be limited; when you bring your own key, usage and cost follow **your** provider’s plan.

---

## Install

The **PyPI package** is **`proofagent-sdk`**; you still **`import proofagent`** in Python.

```bash
pip install proofagent-sdk
```

Install the latest `main` from GitHub without cloning:

```bash
pip install "git+https://github.com/ProofAgent-ai/proofagent-sdk.git"
```

Editable install from a local clone:

```bash
git clone https://github.com/ProofAgent-ai/proofagent-sdk.git
cd proofagent-sdk
pip install -e .
```

Development install with dev dependencies:

```bash
pip install -e ".[dev]"
```

Dependencies include **`httpx`** for async HTTP.

---

## Configuration (environment)

| Variable | Required | Description |
|----------|----------|-------------|
| `PROOFAGENT_API_KEY` | Yes | Project API key (`apk_live_…`). |
| `PROOFAGENT_BASE_URL` | No | Defaults to `https://api.proofagent.ai`. Override for staging or self-hosted. |
| `PROOFAGENT_TIMEOUT_SECONDS` | No | Default `60`. |
| `PROOFAGENT_MAX_RETRIES` | No | Default `3`. |
| `PROOFAGENT_RETRY_BACKOFF_SECONDS` | No | Default `0.75`. |

Optional: `OPENAI_API_KEY` in your own app if you call OpenAI **outside** the SDK; for BYO you pass the key into `start_run` as `llm_api_key`.

```bash
export PROOFAGENT_API_KEY="apk_live_xxx"
# optional
export PROOFAGENT_BASE_URL="https://api.proofagent.ai"
```

---

## Authentication

All requests use:

```http
Authorization: Bearer <PROJECT_API_KEY>
```

With a **project** API key, the backend resolves **tenant + project**; you do **not** need `project_id` in `start_run` for that key.

**JWT** (dashboard user token) is also supported by the API; then you must pass **`project_id`** in the request body for `POST /api/v1/runs`.

---

## Quick start: `ProofAgentClient`

```python
from proofagent import ProofAgentClient
client = ProofAgentClient.from_env()
# or
client = ProofAgentClient(api_key="apk_live_...", base_url="https://api.proofagent.ai")
```

Use as an async context manager for connection reuse:

```python
async with ProofAgentClient.from_env() as client:
    ctx = await client.get_project_context()
```

---

## API surface (SDK methods)

| Method | Purpose |
|--------|---------|
| `ProofAgent.evaluate_sync` / `evaluate` | **Judge-Led Evaluation** — JSON `TestedAgent` + handler/endpoint; optional `reasoning_*` → Judge LLM. |
| `ProofAgent.evaluate_logs_sync` / `evaluate_logs` | **Log-Based Evaluation** — logs + metadata-only `TestedAgent`. |
| `ProofAgentClient.evaluate` / `evaluate_logs` | Same flows on the low-level client (`llm_*` kwargs). |
| `get_project_context()` | Project + `agent_config`, `tools_config`, `internal_agents_config` for the current API key. |
| `get_billing()` | Plan, usage, `max_turns_per_run`, etc. |
| `start_run(...)` | Create a run (Judge-Led or Log-Based). |
| `get_run_status(run_id)` | Status, turns, optional partial result when completed. |
| `get_next_question(run_id)` | Next judge question (Judge-Led only). |
| `submit_turn(run_id, turn_index=..., agent_answer=...)` | Submit agent answer (turn index ≥ 1). |
| `finalize(run_id)` | Trigger final scoring. |
| `get_report(run_id)` | Full report after completion. |
| `poll_until_ready(run_id, ...)` | Poll until run is ready for questions. |
| `poll_until_complete(run_id, ...)` | Poll until status is `completed` (e.g. Log-Based). |

---

## Response envelope

Successful JSON responses follow:

```json
{
  "status": "success",
  "data": { ... },
  "request_id": "..."
}
```

Errors are typically HTTP 4xx/5xx with a `detail` object (or string) containing `error` and `message` codes.

---

## Judge-Led Evaluation (recommended entrypoint)

JSON config + handler; **`ProofAgent`** sets Judge LLM defaults (`reasoning_*` → `llm_*`).

```python
import os
from proofagent import ProofAgent, TestedAgent

tested_agent_config = {
    "role": "customer_support",
    "description": "Support assistant",
    "tools": [{"name": "lookup", "description": "..."}],
}

def handler(message: str) -> str:
    return "..."

your_agent = TestedAgent.from_json(tested_agent_config, handler=handler)
pa = ProofAgent.from_env(
    reasoning_provider="openai",
    reasoning_model="gpt-4o-mini",
    reasoning_api_key=os.environ.get("OPENAI_API_KEY"),
)

result = pa.evaluate_sync(your_agent=your_agent, turns=5, verbose=True)
report = result.report
```

Lower-level: `ProofAgentClient` + `start_run` → `poll_until_ready` → turn loop → `finalize` → `get_report`.

---

## Log-Based Evaluation

```python
from proofagent import ProofAgent, TestedAgent

logs = [{"turn_index": 1, "user_message": "...", "agent_answer": "..."}]

tested_agent_config = {"role": "r", "description": "...", "tools": []}
your_agent = TestedAgent.from_json(tested_agent_config)

pa = ProofAgent.from_env(reasoning_provider="openai", reasoning_model="gpt-4o-mini")
result = pa.evaluate_logs_sync(logs, your_agent, verbose=True)
```

`evaluate_logs` calls `assert_project_supports_logs` before starting.

---

## Exceptions

`ProofAgentError` exposes `message`, `status_code`, `code`, and `payload` for debugging.

---

## Further reading

- `README.md` — install, packaging, Makefile.
- `docs/api.md` — short API reference.
- `docs/quickstart.md` — minimal runnable snippet.
- `examples/judge_led_quickstart.py`, `examples/log_based_evaluation.py` — runnable scripts.
- `notebooks/` — Jupyter walkthroughs (including LangGraph + Judge examples).

For REST details beyond the SDK, see your deployment’s API reference (e.g. `docs/api-reference.md` in the backend repository if available).
