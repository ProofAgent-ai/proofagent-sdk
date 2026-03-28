"""Notebook/example helpers beyond the core SDK (e.g. verbose polling).

Report pretty-printing lives in ``proofagent.report_display``; re-exported here for repo scripts
that add ``examples/`` to ``sys.path`` only.
"""

from __future__ import annotations

import asyncio
from typing import Any

from proofagent.exceptions import ProofAgentError
from proofagent.project_support import LOG_BASED_PROJECT_MODES, assert_project_supports_logs
from proofagent.report_display import (
    extract_report_parts,
    print_aggregate_result,
    print_full_evaluation_report,
    print_metadata_block,
    print_run_header,
    print_turn_transcript,
)


def _maybe_stuck_judge_led(s: str, turns_done: object, waited: float) -> bool:
    """Heuristic: judge-led misconfiguration shows plan_ready + zero turns for a long time."""
    if waited < 45.0:
        return False
    try:
        td = int(turns_done) if turns_done is not None else 0
    except (TypeError, ValueError):
        td = 0
    return td == 0 and s in ("planning", "plan_ready")


def print_live_turn_banner(
    turn_index: int,
    total_turns: int,
    *,
    phase: str = "submitting",
) -> None:
    """
    Print progress during an interactive judge-led loop (before the final report).

    phase: short label, e.g. 'fetching_question', 'submitting', 'done'.
    """
    pct = 100.0 * turn_index / total_turns if total_turns else 0.0
    bar_w = 24
    filled = int(bar_w * turn_index / total_turns) if total_turns else 0
    bar = "█" * filled + "░" * (bar_w - filled)
    print(f"\n{'─'*56}")
    print(f"  Progress │ {bar} │ {pct:5.1f}%")
    print(f"  Turn     │ {turn_index} / {total_turns}  (phase: {phase})")
    print(f"{'─'*56}")


async def poll_until_complete_verbose(
    client: Any,
    run_id: str,
    *,
    timeout_seconds: float = 900.0,
    poll_every_seconds: float = 3.0,
) -> dict[str, Any]:
    """
    Like ProofAgentClient.poll_until_complete but prints status / turn progress while waiting.

    Use for log-based runs that can take several minutes (LLM scoring).
    """
    waited = 0.0
    while waited <= timeout_seconds:
        status = await client.get_run_status(run_id)
        data = status.get("data") or {}
        s = str(data.get("status", "")).lower()
        turns_done = data.get("turns_completed")
        total = data.get("total_turns")
        extra = ""
        if turns_done is not None and total is not None:
            extra = f"  │  turns_completed: {turns_done} / {total}"
        print(f"  [{waited:6.0f}s]  status={s}{extra}")
        if s == "completed":
            return status
        if s == "failed":
            raise ProofAgentError("Run failed", payload=status)
        if _maybe_stuck_judge_led(s, turns_done, waited):
            raise ProofAgentError(
                "Run looks stuck in judge-led planning (status="
                f"{s!r}, turns_completed=0). "
                "For log-based evaluation, use a project with mode log_replay, context_eval, or multi_log "
                "and call assert_project_supports_logs(client) before start_run(logs=[...]). "
                "See examples/log_based_evaluation.py and docs/python-sdk-guide.md.",
                payload=status,
            )
        await asyncio.sleep(poll_every_seconds)
        waited += poll_every_seconds
    raise ProofAgentError(f"Timeout waiting for run completion ({timeout_seconds}s)")
