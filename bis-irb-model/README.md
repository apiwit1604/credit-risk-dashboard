# BIS / Basel Single-Factor IRB Model

Closed-form implementation of the Basel Committee's Internal Ratings-Based (IRB) capital formula
for a corporate exposure, using the Basel single-factor Gaussian copula (Vasicek) calibration.

**This is not a Monte Carlo model.** There's no simulation and no empirical percentile — the
99.9% confidence level is a fixed regulatory constant baked into the formula.

## Run

```bash
python bis_irb_model.py
```

## Use as a library

```python
from bis_irb_model import get_single_factor_bis

result = get_single_factor_bis(lgd=0.40, pd=0.10)   # decimal fractions, not percentages
print(result["Capital Requirement"], result["Correlation"], result["Expected Loss"], result["CVaR"])
```

`lgd` and `pd` must be decimal fractions (`0.40`, not `40`) — passing an out-of-range value now
raises a `ValueError` instead of silently producing a meaningless result, which was possible in
the original script (`LGD=40` ran without error but corresponded to a 4,000% loss severity).

## Why alpha can't be changed here

Basel's IRB formula hardcodes `norm.ppf(0.999)` — this **is** the 99.9% solvency standard Basel
requires banks to hold capital against. It isn't a tunable input the way Monte Carlo VaR
percentiles are in the CreditMetrics and KMV models in this repo. If you need capital at a
different confidence level for internal (non-regulatory) purposes, that's a different — and
non-Basel-compliant — calculation, and should be clearly labeled as such if you build it.

See the repository root [README](../README.md) for the full alpha-comparability discussion.
