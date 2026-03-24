from __future__ import annotations

import os
from dataclasses import dataclass

from ._version import __version__


@dataclass(slots=True)
class ProofAgentConfig:
    api_key: str
    base_url: str = "https://api.proofagent.ai"
    timeout_seconds: float = 60.0
    max_retries: int = 3
    retry_backoff_seconds: float = 0.75
    user_agent: str = f"proofagent/{__version__}"

    @classmethod
    def from_env(cls) -> "ProofAgentConfig":
        api_key = (os.getenv("PROOFAGENT_API_KEY") or "").strip()
        if not api_key:
            raise ValueError("Missing PROOFAGENT_API_KEY")

        base_url = (
            os.getenv("PROOFAGENT_BASE_URL") or "https://api.proofagent.ai"
        ).strip().rstrip("/")
        timeout_seconds = float(os.getenv("PROOFAGENT_TIMEOUT_SECONDS", "60"))
        max_retries = int(os.getenv("PROOFAGENT_MAX_RETRIES", "3"))
        retry_backoff_seconds = float(os.getenv("PROOFAGENT_RETRY_BACKOFF_SECONDS", "0.75"))

        return cls(
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max(0, max_retries),
            retry_backoff_seconds=max(0.0, retry_backoff_seconds),
        )
