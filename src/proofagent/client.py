from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .config import ProofAgentConfig
from .exceptions import ProofAgentError
from .types import InternalAgentConfig, LogEntry, ToolConfig

_RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}


class ProofAgentClient:
    """Async client for the ProofAgent™ API with retries and polling helpers."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
        config: ProofAgentConfig | None = None,
    ):
        cfg = config or ProofAgentConfig.from_env()
        if api_key is not None:
            cfg.api_key = api_key.strip()
        if base_url is not None:
            cfg.base_url = base_url.rstrip("/")
        if timeout_seconds is not None:
            cfg.timeout_seconds = float(timeout_seconds)
        if max_retries is not None:
            cfg.max_retries = max(0, int(max_retries))
        if retry_backoff_seconds is not None:
            cfg.retry_backoff_seconds = max(0.0, float(retry_backoff_seconds))
        if not cfg.api_key:
            raise ValueError("api_key is required")

        self.config = cfg
        self._client: httpx.AsyncClient | None = None

    @classmethod
    def from_env(cls) -> "ProofAgentClient":
        return cls(config=ProofAgentConfig.from_env())

    async def __aenter__(self):
        self._client = self._build_async_client()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.aclose()

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": self.config.user_agent,
        }

    def _build_async_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self.config.timeout_seconds)

    async def aclose(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _parse_error_message(self, data: dict[str, Any], status_code: int) -> tuple[str, str | None]:
        detail = data.get("detail")
        if isinstance(detail, dict):
            return detail.get("message") or f"HTTP {status_code}", detail.get("error")
        if isinstance(detail, str) and detail.strip():
            return detail, data.get("error")
        return (data.get("message") or f"HTTP {status_code}", data.get("error"))

    async def _request(self, method: str, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        client = self._client or self._build_async_client()
        owns_client = self._client is None
        try:
            last_exc: Exception | None = None
            for attempt in range(self.config.max_retries + 1):
                try:
                    resp = await client.request(
                        method=method,
                        url=f"{self.config.base_url}{path}",
                        headers=self._build_headers(),
                        json=json_body,
                    )
                    try:
                        data: dict[str, Any] = resp.json()
                    except Exception:
                        data = {"message": resp.text}

                    if resp.status_code >= 400:
                        message, code = self._parse_error_message(data, resp.status_code)
                        err = ProofAgentError(message=message, status_code=resp.status_code, code=code, payload=data)
                        if resp.status_code in _RETRYABLE_STATUS and attempt < self.config.max_retries:
                            await asyncio.sleep(self.config.retry_backoff_seconds * (2**attempt))
                            continue
                        raise err
                    return data
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    last_exc = exc
                    if attempt < self.config.max_retries:
                        await asyncio.sleep(self.config.retry_backoff_seconds * (2**attempt))
                        continue
                    raise ProofAgentError(f"Network error: {exc}") from exc
            raise ProofAgentError(f"Request failed after retries: {last_exc}")
        finally:
            if owns_client:
                await client.aclose()

    async def get_project_context(self) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/project/context")

    async def get_billing(self) -> dict[str, Any]:
        return await self._request("GET", "/api/billing/invoices")

    async def start_run(
        self,
        *,
        project_id: str | None = None,
        logs: list[LogEntry] | None = None,
        turn_count: int | None = None,
        llm_api_key: str | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        agent_role: str | None = None,
        tools: list[ToolConfig] | None = None,
        internal_agents: list[InternalAgentConfig] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if project_id:
            payload["project_id"] = project_id
        if logs is not None:
            payload["logs"] = logs
        if turn_count is not None:
            payload["turn_count"] = int(turn_count)
        if llm_api_key:
            payload["llm_api_key"] = llm_api_key
        if llm_provider:
            payload["llm_provider"] = llm_provider
        if llm_model:
            payload["llm_model"] = llm_model
        if agent_role is not None:
            payload["agent_role"] = agent_role
        if tools is not None:
            payload["tools"] = tools
        if internal_agents is not None:
            payload["internal_agents"] = internal_agents
        return await self._request("POST", "/api/v1/runs", payload)

    async def get_run_status(self, run_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/v1/runs/{run_id}")

    async def get_next_question(self, run_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/v1/runs/{run_id}/next-question")

    async def submit_turn(
        self,
        run_id: str,
        *,
        turn_index: int,
        agent_answer: str,
        logs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"turn_index": turn_index, "agent_answer": agent_answer}
        if logs is not None:
            body["logs"] = logs
        return await self._request("POST", f"/api/v1/runs/{run_id}/turns", body)

    async def finalize(self, run_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/api/v1/runs/{run_id}/finalize", {})

    async def get_report(self, run_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/v1/runs/{run_id}/report")

    async def poll_until_ready(
        self,
        run_id: str,
        *,
        timeout_seconds: float = 180.0,
        poll_every_seconds: float = 1.5,
    ) -> dict[str, Any]:
        waited = 0.0
        while waited <= timeout_seconds:
            status = await self.get_run_status(run_id)
            s = str(status.get("data", {}).get("status", "")).lower()
            if s in {"plan_ready", "conducting", "awaiting_response", "completed"}:
                return status
            if s == "failed":
                raise ProofAgentError("Run failed before ready", payload=status)
            await asyncio.sleep(poll_every_seconds)
            waited += poll_every_seconds
        raise ProofAgentError(f"Timeout waiting for run to be ready ({timeout_seconds}s)")

    async def poll_until_complete(
        self,
        run_id: str,
        *,
        timeout_seconds: float = 300.0,
        poll_every_seconds: float = 2.0,
    ) -> dict[str, Any]:
        waited = 0.0
        while waited <= timeout_seconds:
            status = await self.get_run_status(run_id)
            s = str(status.get("data", {}).get("status", "")).lower()
            if s == "completed":
                return status
            if s == "failed":
                raise ProofAgentError("Run failed", payload=status)
            await asyncio.sleep(poll_every_seconds)
            waited += poll_every_seconds
        raise ProofAgentError(f"Timeout waiting for run completion ({timeout_seconds}s)")
