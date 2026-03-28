"""High-level Judge-Led Evaluation and Log-Based Evaluation helpers."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from .tested_agent import TestedAgent
from .types import InternalAgentConfig, LogEntry, ToolConfig

VERBOSE_PREFIX = "[ProofAgent]"


@dataclass(slots=True)
class EvaluationResult:
    """Outcome of :meth:`ProofAgent.evaluate` / :meth:`ProofAgentClient.evaluate` (and log-based variants)."""

    run_id: str
    report: dict[str, Any]

    @property
    def score(self) -> Any:
        """``final_score`` from the report envelope, if present."""
        data = self.report.get("data")
        if not isinstance(data, dict):
            return None
        result = data.get("result")
        if not isinstance(result, dict):
            return None
        return result.get("final_score")

    @property
    def label(self) -> Any:
        """``certification_label`` from the report envelope, if present."""
        data = self.report.get("data")
        if not isinstance(data, dict):
            return None
        result = data.get("result")
        if not isinstance(result, dict):
            return None
        return result.get("certification_label")


def truncate_for_verbose(s: str, max_len: int = 500) -> str:
    one_line = " ".join(s.split())
    if len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 1] + "…"


def resolve_agent_metadata(
    your_agent: Any,
    *,
    agent_role: str | None,
    tools: list[ToolConfig] | None,
    internal_agents: list[InternalAgentConfig] | None,
) -> tuple[str | None, list[ToolConfig] | None, list[InternalAgentConfig] | None]:
    if isinstance(your_agent, TestedAgent):
        r = agent_role or your_agent.agent_role_string()
        t = tools if tools is not None else your_agent.tools
        ia = internal_agents if internal_agents is not None else your_agent.internal_agents
        r_out = str(r).strip() if r is not None and str(r).strip() else None
        t_out: list[ToolConfig] | None = t if isinstance(t, list) or t is None else None
        ia_out: list[InternalAgentConfig] | None = ia if isinstance(ia, list) or ia is None else None
        return r_out, t_out, ia_out

    role = agent_role
    if role is None:
        role = getattr(your_agent, "role", None) or getattr(your_agent, "agent_role", None)
    t = tools if tools is not None else getattr(your_agent, "tools", None)
    ia = internal_agents if internal_agents is not None else getattr(your_agent, "internal_agents", None)
    t_out: list[ToolConfig] | None = t if isinstance(t, list) or t is None else None
    ia_out: list[InternalAgentConfig] | None = ia if isinstance(ia, list) or ia is None else None
    r_out = str(role).strip() if role is not None and str(role).strip() else None
    return r_out, t_out, ia_out


def require_agent_role(role: str | None) -> str:
    if not role:
        raise ValueError(
            "Pass agent_role=… or set your_agent.role / your_agent.agent_role on your_agent.",
        )
    return role


async def invoke_your_agent(your_agent: Any, judge_question: str) -> str:
    """Call :class:`TestedAgent` ``respond``, or ``your_agent(judge_question)``, or ``.respond``."""
    if isinstance(your_agent, TestedAgent):
        return await your_agent.respond(judge_question)

    fn: Any = None
    if callable(your_agent) and not isinstance(your_agent, type):
        fn = your_agent
    else:
        respond = getattr(your_agent, "respond", None)
        if callable(respond):
            fn = respond
    if fn is None:
        raise TypeError(
            "your_agent must be callable as your_agent(judge_question: str), or expose "
            "respond(judge_question: str) returning str or awaitable str.",
        )
    out = fn(judge_question)
    if inspect.isawaitable(out):
        out = await out
    return str(out)
