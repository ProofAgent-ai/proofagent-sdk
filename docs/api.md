# API

## `TestedAgent`

JSON-first description of the **tested agent** (your product):

- `TestedAgent.from_json(config, handler=..., endpoint=...)` — `config` uses `role`, `description`, `tools`. For Judge-Led, pass a sync/async **handler** or an **endpoint** URL (POST `{"message": "..."}`).

## `ProofAgent`

Facade over `ProofAgentClient` with optional Judge LLM defaults:

- `ProofAgent.from_env(reasoning_provider=..., reasoning_model=..., reasoning_api_key=...)` — maps to `llm_provider` / `llm_model` / `llm_api_key` (defaults `OPENAI_API_KEY` when reasoning is set).
- `evaluate` / `evaluate_sync`, `evaluate_logs` / `evaluate_logs_sync`

## `EvaluationResult`

Returned by `ProofAgent` / `ProofAgentClient` evaluate helpers:

- `run_id: str`
- `report: dict` — API envelope from `get_report` (typically includes `data`).
- `score` — property: `final_score` from `report["data"]["result"]`
- `label` — property: `certification_label` from the same

## `assert_project_supports_logs`

```python
from proofagent import assert_project_supports_logs

await assert_project_supports_logs(client)
```

Raises `ProofAgentError` if the current project is not Log-Based (`LOG_BASED_PROJECT_MODES`).

## `ProofAgentConfig`

- `api_key`
- `base_url` (default: `https://api.proofagent.ai`)
- `timeout_seconds` (default: `60`)
- `max_retries` (default: `3`)
- `retry_backoff_seconds` (default: `0.75`)

Build from env:

```python
from proofagent import ProofAgentConfig
cfg = ProofAgentConfig.from_env()
```

## `ProofAgentClient`

Create directly:

```python
from proofagent import ProofAgentClient
client = ProofAgentClient(api_key="apk_...", base_url="https://...")
```

From env:

```python
client = ProofAgentClient.from_env()
```

### Methods

- `evaluate(your_agent, *, turns=None, verbose=True, agent_role=None, tools=None, internal_agents=None, project_id=None, llm_api_key=None, llm_provider=None, llm_model=None, poll_ready_timeout=180, poll_ready_every=1.5)` — **Judge-Led Evaluation**
- `evaluate_logs(logs, your_agent, *, verbose=True, agent_role=None, tools=None, internal_agents=None, project_id=None, llm_api_key=None, llm_provider=None, llm_model=None, poll_complete_timeout=900, poll_complete_every=2.0)` — **Log-Based Evaluation**
- `get_project_context()`
- `get_billing()`
- `start_run(project_id=None, logs=None, turn_count=None, llm_api_key=None, llm_provider=None, llm_model=None, agent_role=None, tools=None, internal_agents=None)`
- `get_run_status(run_id)`
- `get_next_question(run_id)`
- `submit_turn(run_id, turn_index, agent_answer, logs=None)`
- `finalize(run_id)`
- `get_report(run_id)`
- `poll_until_ready(run_id, timeout_seconds=180, poll_every_seconds=1.5)`
- `poll_until_complete(run_id, timeout_seconds=300, poll_every_seconds=2.0)`
