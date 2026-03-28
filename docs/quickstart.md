# Quickstart

**Note:** ProofAgent™ is in **beta**. **Bring your own LLM** for Judge reasoning (`ProofAgent.from_env` + `OPENAI_API_KEY`) when you set `reasoning_provider` / `reasoning_model`.

## Install

```bash
pip install proofagent-sdk
```

## Judge-Led Evaluation (default)

**Tested agent** = your product (JSON). **AI Judge** = evaluation system.

```python
from proofagent import ProofAgent, TestedAgent

tested_agent_config = {
    "role": "customer_support",
    "description": "Helpful support assistant",
    "tools": [
        {"name": "policy_lookup", "description": "Policy lookup"},
    ],
}

def your_agent_handler(message: str) -> str:
    return "I can help with that."

your_agent = TestedAgent.from_json(tested_agent_config, handler=your_agent_handler)
pa = ProofAgent.from_env(reasoning_provider="openai", reasoning_model="gpt-4o-mini")

result = pa.evaluate_sync(your_agent=your_agent, turns=3, verbose=True)
print(result.label, result.score)
```

Set `PROOFAGENT_API_KEY` and (for BYO) `OPENAI_API_KEY`.

## Log-Based Evaluation

Use a **Log-Based** project key. Same JSON; omit `handler`.

```python
your_agent = TestedAgent.from_json(tested_agent_config)
result = pa.evaluate_logs_sync(logs, your_agent, verbose=True)
```

See [README.md](https://github.com/ProofAgent-ai/proofagent-sdk/blob/main/README.md) for details.
