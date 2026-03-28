"""
Log-Based Evaluation — historical transcripts (metadata-only tested agent config).

Requires a Log-Based project API key. Optional OPENAI_API_KEY for Judge LLM.
"""

from __future__ import annotations

import os

from proofagent import ProofAgent, TestedAgent, print_full_evaluation_report

tested_agent_config = {
    "role": "billing_support",
    "description": "Billing support assistant focused on accuracy",
    "tools": [
        {"name": "invoice_lookup", "description": "Find invoice records"},
        {"name": "refund_api", "description": "Submit refund requests"},
    ],
}


def main() -> None:
    if not os.environ.get("PROOFAGENT_API_KEY", "").strip():
        raise RuntimeError("Set PROOFAGENT_API_KEY (Log-Based project).")

    logs = [
        {"turn_index": 1, "user_message": "I was charged twice", "agent_answer": "Sorry, let me verify invoices."},
        {"turn_index": 2, "user_message": "Can I get one refunded?", "agent_answer": "Yes, I can start that refund flow."},
        {"turn_index": 3, "user_message": "How long will it take?", "agent_answer": "Usually 3-5 business days."},
    ]

    your_agent = TestedAgent.from_json(tested_agent_config)
    byo = os.environ.get("OPENAI_API_KEY", "").strip()
    pa = ProofAgent.from_env(
        reasoning_provider="openai" if byo else None,
        reasoning_model="gpt-4o-mini" if byo else None,
    )

    result = pa.evaluate_logs_sync(logs, your_agent, verbose=True)
    print(result.label, result.score)
    print("\n--- Run ID ---\n", result.run_id)
    print_full_evaluation_report(result.report)


if __name__ == "__main__":
    main()
