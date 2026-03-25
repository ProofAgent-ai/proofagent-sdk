"""
Log-based end-to-end example (submit full conversation logs).

Install the SDK::

    pip install proofagent-sdk
    pip install "git+https://github.com/ProofAgent-ai/proofagent-sdk.git"
    # or: cd proofagent-sdk && pip install -e .

Import: ``from proofagent import ProofAgentClient``.

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

sys.path.insert(0, str(Path(__file__).parent.resolve()))
from report_helpers import poll_until_complete_verbose, print_full_evaluation_report  # noqa: E402

from proofagent import ProofAgentClient


async def main() -> None:
    api_key = os.environ.get("PROOFAGENT_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Set PROOFAGENT_API_KEY. Optional: set PROOFAGENT_BASE_URL to override the SDK default host.",
        )

    byo_llm_key = os.environ.get("OPENAI_API_KEY", "")

    logs = [
        {"turn_index": 1, "user_message": "I was charged twice", "agent_answer": "Sorry, let me verify invoices."},
        {"turn_index": 2, "user_message": "Can I get one refunded?", "agent_answer": "Yes, I can start that refund flow."},
        {"turn_index": 3, "user_message": "How long will it take?", "agent_answer": "Usually 3-5 business days."},
    ]

    print("Input logs (what you sent):")
    for row in logs:
        print(f"  turn {row['turn_index']}: user={row['user_message']!r} agent={row['agent_answer']!r}")

    async with ProofAgentClient.from_env() as client:
        run = await client.start_run(
            logs=logs,
            llm_api_key=byo_llm_key or None,
            llm_provider="openai" if byo_llm_key else None,
            llm_model="gpt-4o-mini" if byo_llm_key else None,
            agent_role="Billing support assistant focused on accuracy and compliance",
            tools=[
                {"name": "invoice_lookup", "description": "Find invoice records"},
                {"name": "refund_api", "description": "Submit refund requests"},
            ],
        )
        run_id = run["data"]["run_id"]
        print("\nRun started:", run_id)
        print("Polling until completed (verbose; up to 900s)…")

        await poll_until_complete_verbose(client, run_id, timeout_seconds=900.0, poll_every_seconds=3.0)
        report = await client.get_report(run_id)
        print_full_evaluation_report(report)


if __name__ == "__main__":
    asyncio.run(main())
