# API

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
