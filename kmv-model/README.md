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

losses, default_matrix, var, cvar = run_kmv_simulation(
    PORTFOLIO, n_sims=1_000_000, confidence_level=0.99   # adjustable
)
scenario_table = get_scenario_summary(PORTFOLIO, default_matrix, losses)
```

## Key functions

| Function | Purpose |
|---|---|
| `run_kmv_simulation` | Simulate correlated asset paths, flag defaults, compute portfolio VaR/CVaR |
| `get_scenario_summary` | Build a Survive/Default scenario table with probabilities and average loss |

## Note on the default confidence level

The original script left `confidence_level=0.783276` as an unexplained default. This version
sets `DEFAULT_CONFIDENCE_LEVEL = 0.999` instead, to align with the BIS model's regulatory
standard and avoid an unexplained number sitting in a portfolio piece — but it's a fully
adjustable parameter, so set it to whatever alpha you're comparing against.

See the repository root [README](../README.md) for the full alpha-comparability discussion
against the CreditMetrics and BIS models.
