# ProofAgent™ Python SDK

Production-grade async SDK for running ProofAgent™ evaluations with minimal setup.

**Platform:** ProofAgent™ is in **beta**. Only the **free tier** is available at the moment. **Bring your own LLM** for the ProofAgent AI Judge—provide provider credentials in `start_run`; Judge model calls are billed by **your** LLM provider.

**Install:** `pip install proofagent-sdk` — import `from proofagent import ProofAgentClient`. From Git: `pip install "git+https://github.com/ProofAgent-ai/proofagent-sdk.git"`. See [README](https://github.com/ProofAgent-ai/proofagent-sdk#installation).

![ProofAgent™ Logo](assets/proofagent-logo.svg)

## Highlights

- Environment-based config (`PROOFAGENT_API_KEY`, `PROOFAGENT_BASE_URL`)
- Retry-aware HTTP client (network errors + retryable status codes)
- End-to-end helpers:
  - connect and inspect project/billing
  - start run
  - run turn loop
  - finalize and fetch report
- Examples and notebook included
