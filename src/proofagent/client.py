from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .config import ProofAgentConfig
from .evaluation import (
    EvaluationResult,
    invoke_your_agent,
    require_agent_role,
    resolve_agent_metadata,
    truncate_for_verbose,
    VERBOSE_PREFIX,
)
from .exceptions import ProofAgentError
from .project_support import assert_project_supports_logs
from .tested_agent import TestedAgent
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
        if isinstance(detail, list) and detail:
            parts: list[str] = []
            for item in detail:
                if isinstance(item, dict):
                    loc = item.get("loc")
                    msg = item.get("msg") or str(item)
                    ctx = item.get("ctx") if isinstance(item.get("ctx"), dict) else {}
                    extra = ctx.get("given") or ctx.get("reason")
                    if isinstance(loc, (list, tuple)):
                        loc_s = ".".join(str(x) for x in loc)
                    else:
                        loc_s = str(loc) if loc else ""
                    bit = f"{loc_s}: {msg}" if loc_s else msg
                    if extra is not None:
                        bit = f"{bit} ({extra})"
                    parts.append(bit)
                else:
                    parts.append(str(item))
            body = "; ".join(parts) if parts else f"HTTP {status_code}"
            return body, data.get("error")
        if isinstance(detail, dict):
            return detail.get("message") or f"HTTP {status_code}", detail.get("error")
        if isinstance(detail, str) and detail.strip():
            return detail, data.get("error")
        return (data.get("message") or f"HTTP {status_code}", data.get("error"))

    @staticmethod
    def _normalize_tools(tools: list[ToolConfig] | None) -> list[dict[str, Any]] | None:
        """Ensure each tool has an ``id`` (API often requires it); default from ``name``."""
        if tools is None:
            return None
        out: list[dict[str, Any]] = []
        for i, raw in enumerate(tools):
            if not isinstance(raw, dict):
                continue
            t = dict(raw)
            tid = str(t.get("id") or "").strip()
            if not tid:
                t["id"] = str(t.get("name") or f"tool_{i + 1}")
            out.append(t)
        return out

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
            payload["tools"] = self._normalize_tools(tools)
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

    async def evaluate(
        self,
        your_agent: Any,
        *,
        turns: int | None = None,
        verbose: bool = True,
        agent_role: str | None = None,
        tools: list[ToolConfig] | None = None,
        internal_agents: list[InternalAgentConfig] | None = None,
        project_id: str | None = None,
        llm_api_key: str | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        poll_ready_timeout: float = 180.0,
        poll_ready_every: float = 1.5,
    ) -> EvaluationResult:
        """
        **Judge-Led Evaluation** (default tier): the AI Judge drives multi-turn scenarios; your code answers each turn.

        ``your_agent`` must be callable as ``your_agent(judge_question)`` or expose ``respond(judge_question)`` (sync or async).
        Provide **role** via ``agent_role=`` or ``your_agent.role`` / ``your_agent.agent_role``. Optional ``tools`` and
        ``internal_agents`` match the low-level ``start_run`` payload.
        """
        if verbose:
            print(f"{VERBOSE_PREFIX} Starting judge-led evaluation...")

        role, tools_r, internal_r = resolve_agent_metadata(
            your_agent,
            agent_role=agent_role,
            tools=tools,
            internal_agents=internal_agents,
        )
        role = require_agent_role(role)

        if isinstance(your_agent, TestedAgent):
            your_agent.ensure_judge_led_invokable()

        project_ctx = await self.get_project_context()
        billing = await self.get_billing()
        cap = int(billing["data"]["max_turns_per_run"])
        proj = project_ctx.get("data", {}).get("project", {}) or {}
        default_turns = int(proj.get("turn_count", 5))
        if turns is None:
            turn_count = min(default_turns, cap)
        else:
            turn_count = min(int(turns), cap)

        run = await self.start_run(
            project_id=project_id,
            turn_count=turn_count,
            llm_api_key=llm_api_key,
            llm_provider=llm_provider,
            llm_model=llm_model,
            agent_role=role,
            tools=tools_r,
            internal_agents=internal_r,
        )
        run_id = str(run["data"]["run_id"])

        await self.poll_until_ready(
            run_id,
            timeout_seconds=poll_ready_timeout,
            poll_every_seconds=poll_ready_every,
        )
        status = await self.get_run_status(run_id)
        total = int(status["data"]["total_turns"])

        for i in range(1, total + 1):
            q = await self.get_next_question(run_id)
            judge_question = str(q["data"]["judge_question"])
            if verbose:
                print(f"[Turn {i}] AI Judge: {truncate_for_verbose(judge_question)}")
            answer = await invoke_your_agent(your_agent, judge_question)
            if verbose:
                print(f"[Turn {i}] Your Agent: {truncate_for_verbose(answer)}")
            await self.submit_turn(run_id, turn_index=i, agent_answer=answer)

        await self.finalize(run_id)
        report = await self.get_report(run_id)
        return EvaluationResult(run_id=run_id, report=report)

    async def evaluate_logs(
        self,
        logs: list[LogEntry],
        your_agent: Any,
        *,
        verbose: bool = True,
        agent_role: str | None = None,
        tools: list[ToolConfig] | None = None,
        internal_agents: list[InternalAgentConfig] | None = None,
        project_id: str | None = None,
        llm_api_key: str | None = None,
        llm_provider: str | None = None,
        llm_model: str | None = None,
        poll_complete_timeout: float = 900.0,
        poll_complete_every: float = 2.0,
    ) -> EvaluationResult:
        """
        **Log-Based Evaluation**: score historical customer↔agent transcripts (post-production / regression / back-testing).

        Requires a **Log-Based** project API key. ``your_agent`` describes the agent (role, tools) for the run; pass
        ``agent_role=`` or set ``your_agent.role`` / ``your_agent.agent_role``.
        """
        role, tools_r, internal_r = resolve_agent_metadata(
            your_agent,
            agent_role=agent_role,
            tools=tools,
            internal_agents=internal_agents,
        )
        role = require_agent_role(role)

        await assert_project_supports_logs(self)

        if verbose:
            print(f"{VERBOSE_PREFIX} Starting log-based evaluation...")
            print(f"{VERBOSE_PREFIX} Evaluating {len(logs)} historical turns")
            for idx, row in enumerate(logs, start=1):
                ti = row.get("turn_index", idx)
                um = str(row.get("user_message", ""))
                aa = str(row.get("agent_answer", ""))
                print(f"[Turn {ti}] Customer: {truncate_for_verbose(um)}")
                print(f"[Turn {ti}] Agent: {truncate_for_verbose(aa)}")

        run = await self.start_run(
            project_id=project_id,
            logs=logs,
            llm_api_key=llm_api_key,
            llm_provider=llm_provider,
            llm_model=llm_model,
            agent_role=role,
            tools=tools_r,
            internal_agents=internal_r,
        )
        run_id = str(run["data"]["run_id"])

        await self.poll_until_complete(
            run_id,
            timeout_seconds=poll_complete_timeout,
            poll_every_seconds=poll_complete_every,
        )
        report = await self.get_report(run_id)
        return EvaluationResult(run_id=run_id, report=report)

    async def _evaluate_judge_led(self, *args: Any, **kwargs: Any) -> EvaluationResult:
        return await self.evaluate(*args, **kwargs)

    async def _evaluate_log_based(self, *args: Any, **kwargs: Any) -> EvaluationResult:
        return await self.evaluate_logs(*args, **kwargs)
