"""Pretty-print evaluation reports (metadata, scores, turn transcript) — usable from notebooks after ``pip install proofagent-sdk``."""

from __future__ import annotations

from typing import Any


def _report_data(report: dict[str, Any]) -> dict[str, Any]:
    """Unwrap API envelope: prefer `report['data']` when present."""
    data = report.get("data")
    return data if isinstance(data, dict) else report


def extract_report_parts(
    report: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any] | None]:
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
    """Print metadata, aggregate scores, and turn transcript (same layout as ``examples/judge_led_quickstart.py``)."""
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
