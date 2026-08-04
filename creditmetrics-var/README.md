# CreditMetrics — Rating Migration Credit VaR

Monte Carlo simulation of correlated credit rating migrations using a single-factor Gaussian
copula, with each firm's bond cash flows revalued under every possible year-1 rating outcome
(including default) to build a full portfolio loss distribution.

## Run

```bash
python creditmetrics_model.py
```

## Use as a library

```python
from creditmetrics_model import run_full_model

result = run_full_model(alpha=0.99)   # alpha is adjustable — Monte Carlo empirical percentile
print(result["Credit VaR"], result["Expected Loss"], result["Economic Capital"])
```

## Key functions

| Function | Purpose |
|---|---|
| `simulate_rating_outcomes` | Simulate correlated rating migrations per firm |
| `build_value_matrices` | Revalue each firm under every possible rating outcome |
| `compute_scenario_losses` | Map simulated scenarios to portfolio-level losses |
| `compute_credit_var` | Compute Credit VaR / Expected Loss / Economic Capital at a chosen `alpha` |
| `run_full_model` | End-to-end convenience wrapper |

## ⚠️ Known data caveats — verify before production use

The bundled example `PORTFOLIO` has a few `payments_per_year` values that don't match their
inline comments (marked `# TODO` in the source):
- `Firm_2`: commented "Annually" but coded `9`
- `Firm_4`, `Firm_5`: commented "Zero-coupon bond" but coded `4` and `6` (a true zero-coupon
  should be `0`, matching `Firm_3`)

These weren't silently changed — confirm the intended contract terms and update the values
yourself, since they directly affect the cash-flow timing in `value_forward_1y()`.

See the repository root [README](../README.md) for the full alpha-comparability discussion
against the KMV and BIS models.
