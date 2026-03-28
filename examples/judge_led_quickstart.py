"""
Judge-Led Evaluation — quickstart.

- **Tested agent** = your product (JSON config + a small handler).
- **AI Judge** = ProofAgent evaluation (driven by the platform; optional BYO reasoning LLM).

Environment: PROOFAGENT_API_KEY, optional OPENAI_API_KEY for Judge LLM.
"""

from __future__ import annotations

import os

from proofagent import ProofAgent, TestedAgent, print_full_evaluation_report

tested_agent_config = {
    # Short slug must match your project’s allowed role in the ProofAgent dashboard (422 if mismatched).
    "role": "customer_support",
    "description": (
        "IT operations and support agent: triages incidents, looks up ticket status, and answers user "
        "questions with concise, policy-aware replies. (Long text is for your docs; the API uses "
        "`role` above.)"
    ),
    "tools": [
        {"name": "ticket_stub", "description": "Look up ticket status (demo / ITSM integration)."},
    ],
}


def your_agent_handler(message: str) -> str:
    return "I can help with that. Let me check ticket status and policy."


def main() -> None:
    if not os.environ.get("PROOFAGENT_API_KEY", "").strip():
        raise RuntimeError("Set PROOFAGENT_API_KEY.")

    your_agent = TestedAgent.from_json(tested_agent_config, handler=your_agent_handler)

    byo = os.environ.get("OPENAI_API_KEY", "").strip()
    pa = ProofAgent.from_env(
        reasoning_provider="openai" if byo else None,
        reasoning_model="gpt-4o-mini" if byo else None,
    )

    result = pa.evaluate_sync(your_agent=your_agent, turns=3, verbose=True)
    print(result.label, result.score, result.run_id)
    print("\n--- Run ID ---\n", result.run_id)
    print_full_evaluation_report(result.report)


if __name__ == "__main__":
    main()
