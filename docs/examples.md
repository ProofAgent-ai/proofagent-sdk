# Examples

Install the SDK first: `pip install proofagent-sdk` (or `pip install "git+https://github.com/ProofAgent-ai/proofagent-sdk.git"`). Import `from proofagent import ProofAgentClient`.

## Judge-Led Evaluation

```bash
python examples/judge_led_quickstart.py
```

Flow: `ProofAgentClient.evaluate` → AI Judge questions → your agent answers → report.

## Log-Based Evaluation

```bash
python examples/log_based_evaluation.py
```

Flow: historical logs → `ProofAgentClient.evaluate_logs` → report. Requires a Log-Based project API key.

## Notebooks (minimal kickstarts)

| Notebook | Purpose |
|----------|---------|
| `notebooks/simple_e2e.ipynb` | Local: Judge-Led, then Log-Based |
| `notebooks/colab_judge_led.ipynb` | Colab Judge-Led |
| `notebooks/colab_log_based.ipynb` | Colab Log-Based |
| `notebooks/log_based_e2e.ipynb` | Local Log-Based |
| `notebooks/langgraph_react_itops_judge.ipynb` | LangGraph + ProofAgent |
