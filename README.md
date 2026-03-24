<p align="center">
  <img src="assets/proofagent-logo.svg" alt="ProofAgent™" width="400">
</p>

<p align="center">
  <a href="https://pypi.org/project/proofagent-sdk/"><img src="https://img.shields.io/pypi/v/proofagent-sdk" alt="PyPI version"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+"></a>
  <a href="https://www.proofagent.ai/"><img src="https://img.shields.io/badge/docs-proofagent.ai-06B6D4" alt="ProofAgent™"></a>
</p>

# ProofAgent™ Python SDK

Official SDK for the [ProofAgent™](https://www.proofagent.ai/) AI agent evaluation platform. This is the supported Python client for running evaluations, retrieving reports, and integrating ProofAgent™ into your workflows.

**Website:** [https://www.proofagent.ai](https://www.proofagent.ai)

## Install

```bash
pip install proofagent-sdk
```

The **import package name** is `proofagent` (the PyPI distribution name is `proofagent-sdk`).

Development install from a clone:

```bash
pip install -e ".[dev]"
```

## Quick start: CLI

Create a starter config in the current directory:

```bash
proofagent init
```

This prints a short welcome message and writes `proofagent.yaml` (use `-o` / `--output` to pick another path). Set your API key in that file or via `PROOFAGENT_API_KEY`.

## Quick start: Python

```python
import asyncio
import os

from proofagent import ProofAgentClient, __version__

print(__version__)  # e.g. "0.1.0"


async def main() -> None:
    async with ProofAgentClient.from_env() as client:
        byo = os.environ.get("OPENAI_API_KEY", "").strip()
        run = await client.start_run(
            turn_count=3,
            llm_api_key=byo or None,
            llm_provider="openai" if byo else None,
            llm_model="gpt-4o-mini" if byo else None,
            agent_role="Helpful assistant",
        )
        run_id = run["data"]["run_id"]
        print("Started run:", run_id)


asyncio.run(main())
```

The client is **async** (`async`/`await`); use `asyncio.run()` from synchronous scripts.

## Official SDK

This repository publishes **`proofagent-sdk`** on PyPI. Import the package as **`proofagent`**. It is the official Python SDK for ProofAgent™; use it when you want a maintained client aligned with the ProofAgent™ API.

## Documentation and examples

| Resource | Description |
|----------|-------------|
| [docs/python-sdk-guide.md](docs/python-sdk-guide.md) | SDK guide |
| [docs/quickstart.md](docs/quickstart.md) | Short snippets |
| [examples/](examples/) | Runnable examples |

Build docs locally: `make docs-serve`

## Configuration

| Variable | Role |
|----------|------|
| `PROOFAGENT_API_KEY` | API key (required for `ProofAgentClient.from_env()`) |
| `PROOFAGENT_BASE_URL` | API origin (default `https://api.proofagent.ai`) |

See `ProofAgentConfig` in the package for timeouts and retries.

## Package layout

- **`src/proofagent/`** — `ProofAgentClient`, `ProofAgentConfig`, `ProofAgentError`, `types`, CLI (`proofagent` command)
- **Python 3.10+**, **httpx** for async HTTP

## Developer commands

```bash
make install-dev
make lint
make test
make build
```

## Publishing (maintainers)

Use a [PyPI](https://pypi.org) API token with `twine`. Build artifacts land in `dist/`.

```bash
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```
