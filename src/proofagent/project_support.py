"""Project mode checks for Log-Based Evaluation (API key must match project type)."""

from __future__ import annotations

from typing import Any

from .exceptions import ProofAgentError

# Must match backend log-based project modes (dashboard / API).
LOG_BASED_PROJECT_MODES = frozenset({"log_replay", "context_eval", "multi_log"})


async def assert_project_supports_logs(client: Any) -> dict[str, Any]:
    """
    Call before ``evaluate_logs`` / ``start_run(logs=[...])``.

    The API only ingests ``logs`` when the **project** evaluation mode is Log-Based
    (``log_replay``, ``context_eval``, or ``multi_log``). A **Judge-Led Evaluation**
    project ignores ``logs`` and starts an interactive run—polling for ``completed``
    then never finishes without turns.
    """
    ctx = await client.get_project_context()
    data = ctx.get("data") if isinstance(ctx, dict) else None
    proj = (data or {}).get("project") if isinstance(data, dict) else None
    if not isinstance(proj, dict):
        raise ProofAgentError(
            "Could not read project from get_project_context(); cannot verify Log-Based Evaluation.",
            payload=ctx if isinstance(ctx, dict) else {},
        )
    mode = str(proj.get("mode") or "").strip().lower()
    name = proj.get("name") or "(unknown)"
    if mode not in LOG_BASED_PROJECT_MODES:
        raise ProofAgentError(
            "Log-Based Evaluation requires a ProofAgent project whose evaluation mode is "
            "log_replay, context_eval, or multi_log. "
            f"Your project {name!r} has mode {mode!r}. "
            "Create a Log-Based project in the ProofAgent dashboard and use that project's API key.",
            payload=ctx if isinstance(ctx, dict) else {},
        )
    return ctx
