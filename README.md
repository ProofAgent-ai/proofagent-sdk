<p align="center">
  <img src="assets/proofagent-logo.svg" alt="ProofAgent™" width="380">
</p>

<p align="center">
  <a href="https://pypi.org/project/proofagent-sdk/">PyPI</a> •
  <a href="https://github.com/ProofAgent-ai/proofagent-sdk">GitHub</a> •
  <a href="https://www.proofagent.ai/">Website</a> •
  <a href="https://www.proofagent.ai/docs">Documentation</a>
</p>

# ProofAgent™ Python SDK

Official Python SDK for [ProofAgent™](https://www.proofagent.ai/), the AI agent evaluation and certification platform.

This SDK is the **supported Python client** for running evaluations, retrieving reports, and integrating ProofAgent™ into production workflows.

## Platform status (beta)

ProofAgent™ is in **beta**. New accounts are on the **free tier** for now. **Judge evaluations use models from your own LLM provider**—pass `llm_api_key`, `llm_provider`, and `llm_model` in `start_run` so the ProofAgent AI Judge runs on your chosen account; **model usage is charged by your provider**, not bundled into the free platform tier. APIs, limits, and pricing may change as we move toward general availability.

## Links

- **Website:** https://www.proofagent.ai
- **Documentation:** https://www.proofagent.ai/docs
- **GitHub:** https://github.com/ProofAgent-ai/proofagent-sdk
- **PyPI:** https://pypi.org/project/proofagent-sdk/

## Installation

**Package naming**

| | |
|---|---|
| **PyPI distribution** | `proofagent-sdk` |
| **Import package** | `proofagent` |

### From PyPI (recommended)

```bash
pip install proofagent-sdk
```

### From GitHub (latest `main` without cloning)

```bash
pip install "git+https://github.com/ProofAgent-ai/proofagent-sdk.git"
```

### From a local clone (editable)

```bash
git clone https://github.com/ProofAgent-ai/proofagent-sdk.git
cd proofagent-sdk
pip install -e .
```

Development install with extras (lint/tests/docs):

```bash
pip install -e ".[dev]"
```

After any install, import the client as:

```python
from proofagent import ProofAgentClient
```

## ProofAgent AI Agent Judge (domain scoring)

The **ProofAgent AI Agent Judge** is more than a generic LLM chat score. It combines:

- **Domain scoring techniques** — rubrics and pipelines aligned to your project (tier, mode, configured metrics).
- **Domain vertical knowledge** — evaluation context grounded in your project’s **domain** (e.g. customer support, finance, cybersecurity) so judge questions, traps, and scoring stay **relevant** to real workflows.
- **Structured Tier 1 metrics** — every completed run can surface scores across dimensions such as:

| Metric key | What it captures |
|------------|------------------|
| `task_success` | Completion of the intended objective |
| `relevance` | Response appropriateness to the user and context |
| `hallucination_factuality` | Accuracy and groundedness of claims |
| `safety` | Harmful or unsafe content |
| `policy_compliance` | Adherence to business / policy rules |
| `tone_and_empathy` | Communication quality and empathy |
| `reasoning_quality` | Logic and coherence |
| `drift_memory_stability` | Consistency and context retention across turns |
| `manipulation_resistance` | Resistance to prompt injection and coercion |
| `coordination_quality` | Multi-agent coordination (when applicable) |
| `tool_picking_quality` | Appropriate tool selection (when tools are in scope) |

Exact keys and aliases in API responses may vary slightly by API version; see your run report’s `summary_scores` / `metric_evaluations`.

ProofAgent’s **proprietary domain scoring layer** sits on top of whichever LLM provider you use for BYO: the Judge still applies domain rubrics and metrics regardless of provider support status below.

## Supported BYO LLMs for the Judge

When you pass `llm_api_key`, `llm_provider`, and `llm_model` into `start_run`, the Judge uses that model for planning, conducting, and scoring for that run. **During beta, expect to supply BYO credentials**; model usage is billed by **your** provider. Fully managed Judge hosting may be limited while we are in beta.

| LLM / provider | BYO in this SDK | Example models | Notes |
|------------------|-----------------|----------------|-------|
| **OpenAI** | **Supported** | `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo` | Use `llm_provider="openai"` and an [OpenAI API key](https://platform.openai.com/api-keys). |
| Anthropic (Claude) | Coming soon | — | Roadmap |
| Google (Gemini) | Coming soon | — | Roadmap |
| Mistral | Coming soon | — | Roadmap |
| Azure OpenAI | Coming soon | — | Roadmap |

**Today, only OpenAI is supported for BYO** through the public API/SDK; additional providers are on the roadmap.

## Quick Start

### CLI

Create a starter config in the current directory:

```bash
proofagent init
```

This command prints a short welcome message and creates `proofagent.yaml`.

You can optionally specify another output path:

```bash
proofagent init --output custom-proofagent.yaml
```

Set your API key in the generated config file or via the `PROOFAGENT_API_KEY` environment variable.

### Python — connect, BYO Judge LLM, run evaluation, read report

Set environment variables (shell or `.env`):

```bash
export PROOFAGENT_API_KEY="apk_live_..."   # project API key from https://www.proofagent.ai
# optional: export PROOFAGENT_BASE_URL="https://api.proofagent.ai"
export OPENAI_API_KEY="sk-..."             # BYO — Judge uses your OpenAI account (usage billed by OpenAI)
```

**1) Connect** — `ProofAgentClient.from_env()` reads `PROOFAGENT_API_KEY` and talks to `https://api.proofagent.ai` by default. Call `get_project_context()` to verify the key and load project/agent settings.

**2) BYO LLM for the AI Judge** — pass `llm_api_key`, `llm_provider="openai"`, and `llm_model` (e.g. `gpt-4o-mini`) into `start_run`. **During beta, plan on supplying these** so Judge calls run on your provider account; usage is charged by your LLM provider.

**3) Client agent** — set the **role**, **tools**, and optional **internal agents** your agent exposes; for **log-based** runs, pass **`logs`** on `start_run` instead of the interactive loop. The API only ingests `logs` when the **project** is in a log-based mode (`log_replay`, `context_eval`, or `multi_log`). A **judge-led** project ignores `logs` and you get an interactive run—polling for `completed` then never finishes without turns. Use a log-based project key, or call `assert_project_supports_logs(client)` from `examples/report_helpers.py` before `start_run(logs=...)`.

**4) Start evaluation** — `start_run` creates a **judge-led** run, or a **log-based** pipeline when `logs` is set **and** the project mode is log-based. Judge-led: `poll_until_ready` → per-turn `get_next_question` / `submit_turn` → `finalize`. Log-based: `poll_until_complete` (or `poll_until_complete_verbose` in examples).

**5) Report** — `get_report` returns scores, transcript, and metadata under `data`. The same evaluations appear in the app at **[https://www.proofagent.ai/dashboard](https://www.proofagent.ai/dashboard)** (list of runs → open a run for the full report).

```python
import asyncio
import json
import os

from proofagent import ProofAgentClient


async def main() -> None:
    async with ProofAgentClient.from_env() as client:
        # --- 1) Establish connection (API key + optional base URL) ---
        ctx = await client.get_project_context()
        proj = ctx.get("data", {}).get("project", {})
        print(f"Connected to ProofAgent — project: {proj.get('name', '?')!r}")

        # --- 2) BYO LLM for the ProofAgent AI Judge (OpenAI supported today) ---
        byo = os.environ.get("OPENAI_API_KEY", "").strip()

        # --- 3) Client agent config (role, tools, optional internal agents; logs = log-based only) ---
        client_agent_role = "Helpful support assistant"
        client_tools = [
            {"name": "policy_lookup", "description": "Retrieve policy clauses for the user"},
            {"name": "ticket_status", "description": "Look up ticket and escalation status"},
        ]
        client_internal_agents = [
            {"id": "policy_agent", "role": "policy", "description": "Policy interpretation helper"},
        ]
        # For log-based scoring, pass logs=[{ "turn_index", "user_message", "agent_answer" }, ...]
        # instead of turn_count + the loop below. Judge-led runs omit `logs`.

        # --- 4) Start judge-led evaluation ---
        run = await client.start_run(
            turn_count=3,
            agent_role=client_agent_role,
            tools=client_tools,
            internal_agents=client_internal_agents,
            llm_api_key=byo or None,
            llm_provider="openai" if byo else None,
            llm_model="gpt-4o-mini" if byo else None,
        )
        run_id = run["data"]["run_id"]
        print(f"Run started: {run_id}")

        await client.poll_until_ready(run_id)
        status = await client.get_run_status(run_id)
        total = int(status["data"]["total_turns"])

        for i in range(1, total + 1):
            q = await client.get_next_question(run_id)
            judge_question = q["data"]["judge_question"]
            await client.submit_turn(
                run_id,
                turn_index=i,
                agent_answer=f"[demo] Responding to: {judge_question[:200]}",
            )

        await client.finalize(run_id)

        # --- 5) Fetch and display report ---
        report = await client.get_report(run_id)
        data = report.get("data", {})
        result = data.get("result") or {}

        print("\n--- Aggregate result ---")
        print(f"final_score: {result.get('final_score')}")
        print(f"certification_label: {result.get('certification_label')}")
        if result.get("summary_scores"):
            print("summary_scores:", json.dumps(result["summary_scores"], indent=2))
        if result.get("text_summary"):
            print(f"text_summary: {result.get('text_summary')[:500]}…")

        transcript = data.get("transcript") or []
        print(f"\n--- Transcript rows: {len(transcript)} ---")
        for row in transcript[:2]:
            print(json.dumps(row, indent=2)[:800])

        print("\n--- Full report data (truncated) ---")
        print(json.dumps(data, indent=2)[:4000])


if __name__ == "__main__":
    asyncio.run(main())
```

#### Example report shape (`GET /api/v1/runs/:id/report`)

Exact fields depend on backend version and domain; typical **`data`** looks like:

```json
{
  "result": {
    "final_score": 8.4,
    "certification_label": "CERTIFIED",
    "summary_scores": {
      "task_success": 8.5,
      "safety": 9.0,
      "policy_compliance": 8.0
    },
    "flags": [],
    "text_summary": "Short narrative from the AI Judge…"
  },
  "transcript": [
    {
      "turn": 1,
      "judge_question": "…",
      "agent_answer": "…"
    }
  ],
  "metadata": {
    "total_turns": 3,
    "evaluated_at": "2026-03-24T12:00:00Z"
  }
}
```

**View reports in the product:** [https://www.proofagent.ai/dashboard](https://www.proofagent.ai/dashboard)

Example report:

![Example evaluation report in the ProofAgent dashboard](assets/report.png)

Runnable copies of this flow (with richer printing) live under [`examples/`](examples/) and [`notebooks/`](notebooks/).

The client is **asynchronous** — use `async` / `await` (or `asyncio.run()` as above).

## Why ProofAgent™?

ProofAgent™ is built to help teams evaluate AI agents before deployment by supporting:

- **Correctness** and response quality checks
- **Refusal** and safety validation
- **Tool usage** and execution verification
- **Multi-turn** evaluation flows
- **Production-oriented** reporting and integration

## Official SDK

This repository publishes the official **`proofagent-sdk`** package on PyPI.

Use this SDK when you want a maintained Python client aligned with the ProofAgent™ platform and API.

## Documentation and examples

| Resource | Description |
|----------|-------------|
| [Documentation portal](https://www.proofagent.ai/docs) | Main product and SDK documentation |
| [docs/python-sdk-guide.md](docs/python-sdk-guide.md) | Python SDK guide |
| [docs/quickstart.md](docs/quickstart.md) | Quickstart snippets |
| [examples/](examples/) | Runnable examples |

Build docs locally:

```bash
make docs-serve
```

## Configuration

| Variable | Description |
|----------|-------------|
| `PROOFAGENT_API_KEY` | API key used by `ProofAgentClient.from_env()` |
| `PROOFAGENT_BASE_URL` | API base URL. Defaults to `https://api.proofagent.ai` |

For advanced configuration such as retries and timeouts, see `ProofAgentConfig`.

## Package layout

**`src/proofagent/`** — main SDK package

| Module | Role |
|--------|------|
| `client.py` | API client |
| `config.py` | Configuration handling |
| `exceptions.py` | SDK exceptions |
| `types.py` | Shared SDK types |
| `cli.py` | CLI entrypoint for the `proofagent` command |

**Runtime requirements:** Python 3.10+, **httpx** for async HTTP.

## License

See the [LICENSE](LICENSE) file for details.

## Support

- **Website:** https://www.proofagent.ai
- **Documentation:** https://www.proofagent.ai/docs
- **GitHub Issues:** https://github.com/ProofAgent-ai/proofagent-sdk/issues
