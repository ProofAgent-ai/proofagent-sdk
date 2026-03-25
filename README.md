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

### Python

```python
import asyncio
import os

from proofagent import ProofAgentClient, __version__

print(__version__)


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

The client is **asynchronous** and should be used with `async` / `await`.

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

## Developer commands

```bash
make install-dev
make lint
make test
make build
```

## Publishing

Use a PyPI API token with [twine](https://twine.readthedocs.io/). Build artifacts are generated in `dist/`.

```bash
rm -rf dist/ build/
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

## License

See the [LICENSE](LICENSE) file for details.

## Support

- **Website:** https://www.proofagent.ai
- **Documentation:** https://www.proofagent.ai/docs
- **GitHub Issues:** https://github.com/ProofAgent-ai/proofagent-sdk/issues
