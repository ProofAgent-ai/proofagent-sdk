# Examples

## Judge-led end-to-end

```bash
python examples/e2e_judge_led.py
```

Flow:
1. Connect to API
2. Read project context + billing
3. Define agent role/tools/internal agents
4. Start run and complete turns
5. Finalize and print score + label

## Log-based end-to-end

```bash
python examples/e2e_log_based.py
```

Flow:
1. Provide logs
2. Start run
3. Wait for completion
4. Fetch report and print result

## Notebook

Open:

`notebooks/simple_e2e.ipynb`

The notebook demonstrates connect, display config, define agent context, evaluate, and display results.
