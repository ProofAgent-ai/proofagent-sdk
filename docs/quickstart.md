# Quickstart

## Install

```bash
pip install proofagent
```

Or local:

```bash
pip install -e .
```

## Configure

```bash
export PROOFAGENT_API_KEY="apk_live_xxx"
# optional; SDK defaults to https://api.proofagent.ai
# export PROOFAGENT_BASE_URL="https://staging.example.com"
export OPENAI_API_KEY="sk-..."  # optional BYO
```

## Minimal flow

```python
import asyncio
from proofagent import ProofAgentClient

async def main():
    async with ProofAgentClient.from_env() as client:
        project = await client.get_project_context()
        billing = await client.get_billing()
        cap = int(billing["data"]["max_turns_per_run"])
        default_turns = int(project["data"]["project"].get("turn_count", 5))
        turns = min(default_turns, cap)

        run = await client.start_run(
            turn_count=turns,
            agent_role="Helpful support assistant",
            tools=[{"name": "policy_lookup", "description": "Policy reference"}],
        )
        run_id = run["data"]["run_id"]
        status = await client.poll_until_ready(run_id)

        for i in range(1, int(status["data"]["total_turns"]) + 1):
            q = await client.get_next_question(run_id)
            await client.submit_turn(run_id, turn_index=i, agent_answer=f"Answer: {q['data']['judge_question']}")

        await client.finalize(run_id)
        report = await client.get_report(run_id)
        print(report["data"]["result"]["final_score"])

asyncio.run(main())
```
