# ProofAgent™ Python SDK

Production-grade async SDK for running ProofAgent™ evaluations with minimal setup.

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
