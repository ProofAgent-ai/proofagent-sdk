"""
Judge-led end-to-end example (interactive turns).

Install the SDK (import package is ``proofagent``; PyPI name is ``proofagent-sdk``)::

    pip install proofagent-sdk
    pip install "git+https://github.com/ProofAgent-ai/proofagent-sdk.git"
    # or: cd proofagent-sdk && pip install -e .

Environment:
  PROOFAGENT_API_KEY (required)
  OPENAI_API_KEY (optional BYO — this script passes OpenAI + gpt-4o-mini when set)

This sample uses OpenAI for BYO LLM parameters. Additional providers will be supported soon;
until then, omit OPENAI_API_KEY to rely on platform defaults for model-backed steps.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from report_helpers import print_full_evaluation_report, print_live_turn_banner  # noqa: E402

from proofagent import ProofAgentClient


async def main() -> None:
    api_key = os.environ.get("PROOFAGENT_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Set PROOFAGENT_API_KEY. Optional: set PROOFAGENT_BASE_URL to override the SDK default host.",
        )

    byo_llm_key = os.environ.get("OPENAI_API_KEY", "")

    async with ProofAgentClient.from_env() as client:
        project_ctx = await client.get_project_context()
        billing = await client.get_billing()

        project = project_ctx["data"]["project"]
        cap = int(billing["data"]["max_turns_per_run"])
        turn_count = min(int(project.get("turn_count", 5)), cap)

        print(f"Connected project: {project['name']} ({project['domain']})")
        print(f"Requested turns -> effective: {project.get('turn_count', 5)} -> {turn_count}")

        run = await client.start_run(
            turn_count=turn_count,
            llm_api_key=byo_llm_key or None,
            llm_provider="openai" if byo_llm_key else None,
            llm_model="gpt-4o-mini" if byo_llm_key else None,
            agent_role="Helpful, policy-grounded support assistant",
            tools=[
                {"name": "policy_lookup", "description": "Retrieve policy clauses"},
                {"name": "ticket_status", "description": "Read ticket and escalation status"},
            ],
            internal_agents=[
                {"id": "policy_agent", "role": "policy", "description": "Policy interpretation helper"},
            ],
        )
        run_id = run["data"]["run_id"]
        print("Run started:", run_id)

        status = await client.poll_until_ready(run_id)
        total_turns = int(status["data"]["total_turns"])
        print(f"Judge will run {total_turns} turn(s).")

        for i in range(1, total_turns + 1):
            print_live_turn_banner(i, total_turns, phase="fetching_question")
            q = await client.get_next_question(run_id)
            question = q["data"]["judge_question"]
            answer = f"Answer {i}: We will follow policy and resolve this carefully. Question was: {question}"
            print_live_turn_banner(i, total_turns, phase="submitting")
            await client.submit_turn(run_id, turn_index=i, agent_answer=answer)
            print(f"  ✓ Turn {i}/{total_turns} submitted.")

        await client.finalize(run_id)
        report = await client.get_report(run_id)
        print_full_evaluation_report(report)


if __name__ == "__main__":
    asyncio.run(main())
