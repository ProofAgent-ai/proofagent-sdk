"""High-level ``ProofAgent`` facade: tested agent vs AI Judge, with optional reasoning (LLM) defaults."""

from __future__ import annotations

import asyncio
import concurrent.futures
import os
from typing import Any, Callable, Coroutine, TypeVar

from .client import ProofAgentClient

_T = TypeVar("_T")


def _run_coro_sync(factory: Callable[[], Coroutine[Any, Any, _T]]) -> _T:
    """Run ``asyncio.run(factory())`` unless already inside a loop (e.g. Jupyter); then run in a thread."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(factory())
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(lambda: asyncio.run(factory())).result()
from .config import ProofAgentConfig
from .evaluation import EvaluationResult
from .types import LogEntry


class ProofAgent:
    """
    Entry point for evaluations: **your tested agent** (``TestedAgent``) vs the **AI Judge** (platform).

    Optional ``reasoning_*`` fields map to bring-your-own Judge LLM (``OPENAI_API_KEY`` by default).
    """

    def __init__(
        self,
        client: ProofAgentClient,
        *,
        reasoning_provider: str | None = None,
        reasoning_model: str | None = None,
        reasoning_api_key: str | None = None,
    ) -> None:
        self._client = client
        self._reasoning_provider = reasoning_provider
        self._reasoning_model = reasoning_model
        self._reasoning_api_key = reasoning_api_key

    @property
    def client(self) -> ProofAgentClient:
        """Underlying :class:`ProofAgentClient` (e.g. ``get_project_context``, ``get_billing``)."""
        return self._client

    @classmethod
    def from_env(
        cls,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
        config: ProofAgentConfig | None = None,
        reasoning_provider: str | None = None,
        reasoning_model: str | None = None,
        reasoning_api_key: str | None = None,
    ) -> ProofAgent:
        client = ProofAgentClient(
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
            config=config,
        )
        r_key = reasoning_api_key if reasoning_api_key is not None else os.getenv("OPENAI_API_KEY", "").strip() or None
        return cls(
            client,
            reasoning_provider=reasoning_provider,
            reasoning_model=reasoning_model,
            reasoning_api_key=r_key,
        )

    def _reasoning_kwargs(self) -> dict[str, Any]:
        return {
            "llm_api_key": self._reasoning_api_key,
            "llm_provider": self._reasoning_provider,
            "llm_model": self._reasoning_model,
        }

    async def evaluate(self, your_agent: Any, **kwargs: Any) -> EvaluationResult:
        merged = {**self._reasoning_kwargs(), **kwargs}
        return await self._client.evaluate(your_agent, **merged)

    def evaluate_sync(self, your_agent: Any, **kwargs: Any) -> EvaluationResult:
        """Sync wrapper for :meth:`evaluate`. Safe in Jupyter (no nested ``asyncio.run``)."""
        return _run_coro_sync(lambda: self.evaluate(your_agent, **kwargs))

    async def evaluate_logs(self, logs: list[LogEntry], your_agent: Any, **kwargs: Any) -> EvaluationResult:
        merged = {**self._reasoning_kwargs(), **kwargs}
        return await self._client.evaluate_logs(logs, your_agent, **merged)

    def evaluate_logs_sync(self, logs: list[LogEntry], your_agent: Any, **kwargs: Any) -> EvaluationResult:
        """Sync wrapper for :meth:`evaluate_logs`. Safe in Jupyter."""
        return _run_coro_sync(lambda: self.evaluate_logs(logs, your_agent, **kwargs))

    async def __aenter__(self) -> ProofAgent:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self._client.__aexit__(exc_type, exc, tb)
