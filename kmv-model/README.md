# KMV / Merton Structural Credit VaR

Monte Carlo simulation of firm asset values under Geometric Brownian Motion, with defaults
triggered when simulated assets fall below debt at maturity (the classic Merton/KMV structural
credit model). Firm defaults are correlated through a single systematic market factor.

## Run

```bash
python kmv_model.py
```

## Use as a library

```python
from kmv_model import PORTFOLIO, run_kmv_simulation, get_scenario_summary

results = run_kmv_simulation(PORTFOLIO, N_SIMULATIONS, DEFAULT_CONFIDENCE_LEVEL)
scenario_table = get_scenario_summary(PORTFOLIO, default_matrix, losses)
```

## Key functions

| Function | Purpose |
|---|---|
| `run_kmv_simulation` | Simulate correlated asset paths, flag defaults, compute portfolio VaR/CVaR |
| `get_scenario_summary` | Build a Survive/Default scenario table with probabilities and average loss |

See the repository root [README](../README.md) for the full alpha-comparability discussion
against the CreditMetrics and BIS models.
