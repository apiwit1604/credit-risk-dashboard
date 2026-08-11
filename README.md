# Credit Risk Models — CreditMetrics, KMV, and BIS/Basel IRB

Three independent portfolio credit risk models, each estimating **Credit Value-at-Risk (Credit VaR)**
via a different methodology, packaged as standalone Python modules plus a comparison Jupyter notebook.

| Model | Approach | Folder |
|---|---|---|
| **CreditMetrics** | Monte Carlo — rating migration (single-factor Gaussian copula) | [`creditmetrics-var/`](./creditmetrics-var) |
| **KMV / Merton** | Monte Carlo — structural default (asset value vs. debt) | [`kmv-model/`](./kmv-model) |
| **BIS / Basel IRB** | Closed-form regulatory capital formula | [`bis-irb-model/`](./bis-irb-model) |

A side-by-side comparison notebook lives in [`notebooks/Credit_VaR_Models_Comparison.ipynb`](./notebooks/Credit_VaR_Models_Comparison.ipynb).

## 🇬🇧 Project Overview

This repository packages three independent credit risk models, each estimating portfolio Credit VaR
through a different methodology:

1. **CreditMetrics** — Monte Carlo simulation of firm-level credit rating migrations via a
   single-factor Gaussian copula, with cash flows revalued under each simulated rating outcome.
2. **KMV / Merton Model** — Structural model simulating firm asset value against debt via
   Geometric Brownian Motion; a firm defaults if simulated assets fall below debt at maturity.
3. **BIS / Basel IRB Formula** — The Basel Committee's closed-form Internal Ratings-Based capital
   formula. Not a simulation — a direct analytical calculation per exposure.

### ⚠️ Important: alpha is not comparable across all three models

- **CreditMetrics** and **KMV** are both Monte Carlo models — their confidence level (`alpha`) is a
  free parameter (an empirical loss percentile), so these two **can** be set to the same value and
  compared directly.
- **BIS/Basel IRB is a closed-form regulatory formula fixed at 99.9%** confidence
  (`norm.ppf(0.999)` is hardcoded into the Basel calibration) — it is **not** an adjustable
  parameter. Changing it would no longer represent Basel-compliant regulatory capital.
- So: "same alpha for all three" is achievable for CreditMetrics + KMV; BIS is reported alongside
  at its fixed 99.9%, clearly labeled as such rather than silently forced to match.

See [`notebooks/Credit_VaR_Models_Comparison.ipynb`](./notebooks/Credit_VaR_Models_Comparison.ipynb)
for a working example of this comparison, including a single `ALPHA` variable that drives both
Monte Carlo models consistently.

---

## Repository Structure

```
credit-risk-models/
├── creditmetrics-var/
│   └── creditmetrics_model.py     # Rating migration Monte Carlo Credit VaR
├── kmv-model/
│   └── kmv_model.py               # Structural (Merton/KMV) Monte Carlo Credit VaR
├── bis-irb-model/
│   └── bis_irb_model.py           # Basel IRB closed-form capital formula
├── notebooks/
│   └── Credit_VaR_Models_Comparison.ipynb   # Runs and compares all three models
├── requirements.txt
└── README.md
```

Each model folder is self-contained: import its functions directly, or run the file standalone
(`python creditmetrics_model.py`) for a quick demo with the module's default example portfolio.

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/credit-risk-models.git
cd credit-risk-models

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the Models

**Standalone (quick demo, uses each file's built-in example portfolio):**
```bash
python creditmetrics-var/creditmetrics_model.py
python kmv-model/kmv_model.py
python bis-irb-model/bis_irb_model.py
```

**Comparison notebook (recommended — runs all three together with a shared, adjustable `ALPHA`):**
```bash
jupyter notebook notebooks/Credit_VaR_Models_Comparison.ipynb
```

**As a library, in your own script:**
```python
from creditmetrics_model import run_full_model
result = run_full_model(alpha=0.99)
print(result["Credit VaR"])
```


---
