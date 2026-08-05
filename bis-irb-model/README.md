# BIS / Basel Single-Factor IRB Model

Closed-form implementation of the Basel Committee's Internal Ratings-Based (IRB) capital formula
for a corporate exposure, using the Basel single-factor Gaussian copula (Vasicek) calibration.

## Run

```bash
python bis_irb_model.py
```

## Use as a library

```python
from bis_irb_model import get_single_factor_bis

result = get_single_factor_bis(lgd=40, pd=0.10) 
print(result["Capital Requirement"], result["Correlation"], result["Expected Loss"], result["CVaR"])
```

See the repository root [README](../README.md) for the full alpha-comparability discussion.
