import asyncio

import pytest

from proofagent.evaluation import (
    EvaluationResult,
    invoke_your_agent,
    require_agent_role,
    resolve_agent_metadata,
    truncate_for_verbose,
)
from proofagent.tested_agent import TestedAgent


def test_truncate_for_verbose():
    assert len(truncate_for_verbose("x" * 600)) < 600


def test_resolve_agent_metadata_explicit():
    class A:
        role = "r"
        tools = [{"name": "t", "description": "d"}]

    r, t, ia = resolve_agent_metadata(A(), agent_role=None, tools=None, internal_agents=None)
    assert r == "r"
    assert t is not None and len(t) == 1


def test_require_agent_role_rejects_empty():
    with pytest.raises(ValueError):
        require_agent_role(None)
    with pytest.raises(ValueError):
        require_agent_role("")


def test_invoke_your_agent_async_callable():
    async def f(q: str) -> str:
        return f"ok:{q}"

    assert asyncio.run(invoke_your_agent(f, "hi")) == "ok:hi"


def test_invoke_your_agent_sync_callable():
    assert asyncio.run(invoke_your_agent(lambda q: f"x{q}", "a")) == "xa"


def test_invoke_your_agent_respond_method():
    class B:
        def respond(self, q: str) -> str:
            return q.upper()

    assert asyncio.run(invoke_your_agent(B(), "ab")) == "AB"


def test_invoke_your_agent_tested_agent():
    cfg = {"role": "r", "description": "d", "tools": []}
    ta = TestedAgent.from_json(cfg, handler=lambda m: f"echo:{m}")
    assert asyncio.run(invoke_your_agent(ta, "x")) == "echo:x"


def test_agent_role_string_prefers_short_role():
    cfg = {"role": "customer_support", "description": "Long human description here.", "tools": []}
    ta = TestedAgent.from_json(cfg, handler=lambda m: m)
    assert ta.agent_role_string() == "customer_support"


def test_evaluation_result_score_label():
    er = EvaluationResult(
        run_id="rid",
        report={"data": {"result": {"final_score": 8.5, "certification_label": "CERTIFIED"}}},
    )
    assert er.score == 8.5
    assert er.label == "CERTIFIED"
