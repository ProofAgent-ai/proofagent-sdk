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

**Log-based runs (`start_run(logs=[...])`):** the API only ingests `logs` when the **project’s evaluation mode** is log-based (`log_replay`, `context_eval`, or `multi_log`). A **judge-led** project key will ignore `logs` and start an interactive judge flow—polling for `completed` then appears to hang. Use a log-based project in the dashboard (or call `assert_project_supports_logs(client)` from `examples/report_helpers.py` before `start_run` to fail fast with a clear error).

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

If you omit BYO `llm_api_key`, the platform may use **managed** judge defaults depending on your plan (not guaranteed for all tiers).

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
| `get_project_context()` | Project + `agent_config`, `tools_config`, `internal_agents_config` for the current API key. |
| `get_billing()` | Plan, usage, `max_turns_per_run`, etc. |
| `start_run(...)` | Create a run (judge-led or log-based). |
| `get_run_status(run_id)` | Status, turns, optional partial result when completed. |
| `get_next_question(run_id)` | Next judge question (judge-led only). |
| `submit_turn(run_id, turn_index=..., agent_answer=...)` | Submit agent answer (turn index ≥ 1). |
| `finalize(run_id)` | Trigger final scoring. |
| `get_report(run_id)` | Full report after completion. |
| `poll_until_ready(run_id, ...)` | Poll until run is ready for questions. |
| `poll_until_complete(run_id, ...)` | Poll until status is `completed` (e.g. log-based). |

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

## Judge-led flow (pseudo-code)

```python
async with ProofAgentClient.from_env() as client:
    run = await client.start_run(
        turn_count=5,
        llm_api_key=os.environ["OPENAI_API_KEY"],
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        agent_role="Support assistant",
    )
    run_id = run["data"]["run_id"]
    await client.poll_until_ready(run_id)
    status = await client.get_run_status(run_id)
    total = int(status["data"]["total_turns"])

    for i in range(1, total + 1):
        q = await client.get_next_question(run_id)
        answer = your_agent(q["data"]["judge_question"])
        await client.submit_turn(run_id, turn_index=i, agent_answer=answer)

    await client.finalize(run_id)
    report = await client.get_report(run_id)
```

---

## Log-based flow

```python
from pathlib import Path
import sys
sys.path.insert(0, str(Path("examples")))  # local clone: report_helpers
from report_helpers import assert_project_supports_logs

logs = [
    {"turn_index": 1, "user_message": "...", "agent_answer": "..."},
    ...
]
async with ProofAgentClient.from_env() as client:
    await assert_project_supports_logs(client)
    run = await client.start_run(
        logs=logs,
        llm_api_key=...,
        llm_provider="openai",
        llm_model="gpt-4o-mini",
    )
    await client.poll_until_complete(run["data"]["run_id"])
    report = await client.get_report(run["data"]["run_id"])
```

---

## Exceptions

`ProofAgentError` exposes `message`, `status_code`, `code`, and `payload` for debugging.

---

## Further reading

- `README.md` — install, packaging, Makefile.
- `docs/api.md` — short API reference.
- `docs/quickstart.md` — minimal runnable snippet.
- `examples/e2e_judge_led.py`, `examples/e2e_log_based.py` — runnable scripts.
- `notebooks/` — Jupyter walkthroughs (including LangGraph + Judge examples).

For REST details beyond the SDK, see your deployment’s API reference (e.g. `docs/api-reference.md` in the backend repository if available).
