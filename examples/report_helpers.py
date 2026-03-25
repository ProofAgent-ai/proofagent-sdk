"""Notebook/example helpers — not part of the published ``proofagent`` package API.

Install the client with ``pip install proofagent-sdk`` (import ``from proofagent import …``).
"""

from __future__ import annotations

import asyncio
from typing import Any

from proofagent.exceptions import ProofAgentError

# Must match backend LOG_BASED_MODES (see ProofAgent API / project wizard).
LOG_BASED_PROJECT_MODES = frozenset({"log_replay", "context_eval", "multi_log"})


async def assert_project_supports_logs(client: Any) -> dict[str, Any]:
    """
    Call before ``start_run(logs=[...])``.

    The API only persists ``logs`` when the **project** evaluation mode is log-based
    (e.g. ``log_replay``). If the project is ``judge_led``, logs are ignored and the run
    behaves like judge-led (planning → plan_ready) and never reaches ``completed`` without
    interactive turns—``poll_until_complete`` will spin until timeout.
    """
    ctx = await client.get_project_context()
    data = ctx.get("data") if isinstance(ctx, dict) else None
    proj = (data or {}).get("project") if isinstance(data, dict) else None
    if not isinstance(proj, dict):
        raise ProofAgentError(
            "Could not read project from get_project_context(); cannot verify log-based mode.",
            payload=ctx if isinstance(ctx, dict) else {},
        )
    mode = str(proj.get("mode") or "").strip().lower()
    name = proj.get("name") or "(unknown)"
    if mode not in LOG_BASED_PROJECT_MODES:
        raise ProofAgentError(
            "start_run(logs=[...]) requires a ProofAgent project whose evaluation mode is "
            "log_replay, context_eval, or multi_log. "
            f"Your project {name!r} has mode {mode!r}. "
            "Create a log-based project in the ProofAgent dashboard and use that project's API key.",
            payload=ctx if isinstance(ctx, dict) else {},
        )
    return ctx


def _maybe_stuck_judge_led(s: str, turns_done: object, waited: float) -> bool:
    """Heuristic: judge-led misconfiguration shows plan_ready + zero turns for a long time."""
    if waited < 45.0:
        return False
    try:
        td = int(turns_done) if turns_done is not None else 0
    except (TypeError, ValueError):
        td = 0
    return td == 0 and s in ("planning", "plan_ready")


def _report_data(report: dict[str, Any]) -> dict[str, Any]:
    """Unwrap API envelope: prefer `report['data']` when present."""
    data = report.get("data")
    return data if isinstance(data, dict) else report


def extract_report_parts(report: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any] | None]:
    """
    Return (data dict, transcript rows, metadata dict).

    Backend shape (GET /api/v1/runs/:id/report): data.result, data.transcript, data.metadata.
    """
    data = _report_data(report)
    raw_t = data.get("transcript")
    transcript: list[dict[str, Any]] = [r for r in raw_t if isinstance(r, dict)] if isinstance(raw_t, list) else []
    meta = data.get("metadata")
    meta_out = meta if isinstance(meta, dict) else None
    return data, transcript, meta_out


def print_run_header(run_id: str, mode: str | None = None, total_turns: int | None = None) -> None:
    """Print a compact run identity line for notebooks."""
    parts = [f"Run ID: {run_id}"]
    if mode:
        parts.append(f"mode={mode}")
    if total_turns is not None:
        parts.append(f"planned_turns={total_turns}")
    print("\n" + " ┃ ".join(parts))


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


def print_aggregate_result(report: dict[str, Any]) -> None:
    """Print final_score, certification_label, summary_scores, text_summary from report data."""
    data, _, _ = extract_report_parts(report)
    result = data.get("result") or {}
    print("\n" + "=" * 56)
    print("  Aggregate evaluation result")
    print("=" * 56)
    if "final_score" in result:
        print(f"  Final score:           {result.get('final_score')}")
    if result.get("certification_label") is not None:
        print(f"  Certification label:   {result.get('certification_label')}")
    if result.get("summary_scores"):
        print("  Summary scores (by dimension):")
        for k, v in (result.get("summary_scores") or {}).items():
            print(f"    • {k}: {v}")
    if result.get("flags"):
        print(f"  Flags:                 {result.get('flags')}")
    ts = result.get("text_summary")
    if ts:
        print("\n  AI judge summary:")
        print(f"  {ts}")


def print_metadata_block(report: dict[str, Any]) -> None:
    """Print data.metadata when present (total_turns, evaluated_at, models_used, etc.)."""
    _, _, meta = extract_report_parts(report)
    if not meta:
        return
    print("\n" + "-" * 56)
    print("  Report metadata")
    print("-" * 56)
    for key in ("total_turns", "evaluated_at", "billing_period"):
        if key in meta and meta[key] is not None:
            print(f"  {key}: {meta[key]}")
    if meta.get("models_used"):
        print(f"  models_used: {meta['models_used']}")


def print_turn_transcript(
    report: dict[str, Any],
    *,
    max_chars: int = 2000,
    title: str | None = None,
) -> None:
    """
    Print per-turn lines from the report `transcript` (turn, question, answer, conductor_notes).

    Shows **Turn N of M** using `metadata.total_turns` when available, else inferred from rows.
    """
    data, turns, meta = extract_report_parts(report)

    if not turns:
        keys = list(data.keys()) if isinstance(data, dict) else []
        print(
            "\n[No turn-level `transcript` in this report. "
            f"If your API returns it, it will appear here. Data keys: {keys}]",
        )
        return

    total_planned: int | None = None
    if meta and meta.get("total_turns") is not None:
        total_planned = int(meta["total_turns"])

    n_recorded = len(turns)
    header = title or "Turn-level transcript (judge ↔ agent)"
    print("\n" + "=" * 56)
    print(f"  {header}")
    print(f"  Recorded turns: {n_recorded}" + (f" │ Planned cap: {total_planned}" if total_planned else ""))
    print("=" * 56)

    for step, row in enumerate(turns, start=1):
        t = row.get("turn", step)
        denom = total_planned if total_planned else n_recorded
        print(f"\n  ┌─ Turn {t} of {denom}  (row {step}/{n_recorded})")
        q = str(row.get("question", ""))[:max_chars]
        a = str(row.get("answer", ""))[:max_chars]
        print(f"  │  Judge / question:\n  │    {q}")
        print(f"  │  Agent answer:\n  │    {a}")
        notes = row.get("conductor_notes")
        if notes is not None and str(notes).strip():
            print(f"  │  Conductor notes:\n  │    {str(notes)[:max_chars]}")
        print("  └" + "─" * 52)


def print_full_evaluation_report(report: dict[str, Any], *, max_chars: int = 2000) -> None:
    """Convenience: metadata + aggregate scores + turn transcript."""
    data, _, meta = extract_report_parts(report)
    rid = data.get("run_id", "?")
    mode = data.get("mode")
    tt = None
    if meta and meta.get("total_turns") is not None:
        tt = int(meta["total_turns"])
    print_run_header(str(rid), mode=str(mode) if mode else None, total_turns=tt)
    print_metadata_block(report)
    print_aggregate_result(report)
    print_turn_transcript(report, max_chars=max_chars)


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
                "See examples/e2e_log_based.py and docs/python-sdk-guide.md.",
                payload=status,
            )
        await asyncio.sleep(poll_every_seconds)
        waited += poll_every_seconds
    raise ProofAgentError(f"Timeout waiting for run completion ({timeout_seconds}s)")
