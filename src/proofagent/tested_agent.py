"""JSON-first definition of the agent under test (your agent vs the AI Judge)."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx

from .types import InternalAgentConfig, ToolConfig


@dataclass
class TestedAgent:
    """
    The **tested agent** (your product): config from JSON plus either a **handler** or an **endpoint**.

    The **AI Judge** is the evaluation system; it is not configured here.
    """

    __test__ = False  # not a pytest test class (name matches Test*)

    role: str
    description: str
    tools: list[ToolConfig]
    internal_agents: list[InternalAgentConfig] | None = None
    _handler: Callable[[str], Any] | None = field(default=None, repr=False)
    _endpoint: str | None = field(default=None, repr=False)

    @classmethod
    def from_json(
        cls,
        config: dict[str, Any],
        *,
        handler: Callable[[str], Any] | None = None,
        endpoint: str | None = None,
        internal_agents: list[InternalAgentConfig] | None = None,
    ) -> TestedAgent:
        """
        Build from a JSON-style dict (``role``, ``description``, ``tools``).

        For **Judge-Led Evaluation**, pass ``handler=`` *or* ``endpoint=``.
        For **Log-Based Evaluation** (metadata only), you may omit both.
        """
        if handler is not None and endpoint is not None:
            raise ValueError("Pass only one of handler= or endpoint=")
        raw_tools = config.get("tools")
        tools: list[ToolConfig] = raw_tools if isinstance(raw_tools, list) else []
        role = str(config.get("role") or "").strip()
        description = str(config.get("description") or "").strip()
        return cls(
            role=role,
            description=description,
            tools=tools,
            internal_agents=internal_agents,
            _handler=handler,
            _endpoint=endpoint.strip() if isinstance(endpoint, str) and endpoint.strip() else None,
        )

    def agent_role_string(self) -> str:
        """
        String sent to the API as ``agent_role``.

        The backend validates this field (length / allowed roles). Prefer the short ``role`` slug
        (e.g. ``customer_support``); use ``description`` only when ``role`` is empty.
        """
        role = str(self.role or "").strip()
        if role:
            return role
        desc = str(self.description or "").strip()
        if desc:
            return desc
        return ""

    def ensure_judge_led_invokable(self) -> None:
        if self._handler is None and self._endpoint is None:
            raise ValueError(
                "Judge-Led Evaluation needs a response path: use "
                "TestedAgent.from_json(..., handler=your_function) or endpoint=https://...",
            )

    async def respond(self, message: str) -> str:
        self.ensure_judge_led_invokable()
        if self._handler is not None:
            out = self._handler(message)
            if inspect.isawaitable(out):
                out = await out
            return str(out)
        assert self._endpoint is not None
        return await self._respond_http(message)

    async def _respond_http(self, message: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(self._endpoint, json={"message": message})
            resp.raise_for_status()
            try:
                data = resp.json()
            except Exception:
                return resp.text
            if isinstance(data, str):
                return data
            if isinstance(data, dict):
                for key in ("reply", "response", "text", "answer", "agent_answer", "content"):
                    v = data.get(key)
                    if v is not None and str(v).strip():
                        return str(v)
            return str(data)
