# Credit Risk Toolkit

A small, from-scratch toolkit of quantitative credit-risk models —
reduced-form bond-implied PD, the Merton structural model, KMV portfolio
Monte Carlo, a CreditMetrics-style ratings-migration Credit VaR engine,
and the Basel IRB single-factor capital formula — plus an interactive
Streamlit dashboard to explore each one.

## Why this exists

Six standalone research notebooks were consolidated into a single,
importable, tested package with math documentation and an interactive
front end, so the models can actually be reused (and reviewed) rather
than re-copy-pasted per notebook.

## ⚠️ Read this first

Two of the models in this repo use **different, incompatible
conventions** for "asset correlation" (`rho` directly vs. `R = rho²`).
This was **not** silently fixed — see
**[docs/06_correlation_conventions.md](docs/06_correlation_conventions.md)**
before comparing numbers across `kmv_montecarlo.py` /
`basel_single_factor.py` and `credit_var_ratings.py`.

## Repository structure

```
credit-risk-toolkit/
├── credit_risk/                  # the package — pure logic, no UI
│   ├── bond_pd.py                 # PD from credit-spread bootstrap
│   ├── bond_calibration.py        # PD calibrated to a market bond price
│   ├── merton.py                  # Merton (1974) structural PD
│   ├── kmv_montecarlo.py          # KMV portfolio Monte Carlo (VaR/CVaR/EC)
│   ├── credit_var_ratings.py      # CreditMetrics ratings-migration Credit VaR
│   ├── basel_single_factor.py     # Basel IRB / ASRF regulatory capital
│   └── sample_data.py             # shared demo inputs used by docs & dashboard
├── docs/                          # math derivation + design notes, one per model
│   ├── 01_bond_implied_pd.md
│   ├── 02_merton_structural.md
│   ├── 03_kmv_montecarlo.md
│   ├── 04_credit_var_ratings.md
│   ├── 05_basel_single_factor.md
│   └── 06_correlation_conventions.md   # <- read this one
├── app.py                         # Streamlit dashboard home page
├── pages/                         # one Streamlit page per model
├── requirements.txt
└── README.md
```

## Model → theory map

| Page | Model | Core idea |
|---|---|---|
| Bond-Implied PD — Credit Spread | Reduced-form | PD from the ratio of a risky vs. riskless bond price |
| Bond-Implied PD — Price Calibration | Reduced-form | PD calibrated so model price = observed market price |
| Merton Structural Model | Structural | Equity as a call option on firm assets |
| KMV Portfolio Monte Carlo | Structural, simulated | Merton model + correlated firms, simulated to a portfolio loss distribution |
| Credit VaR — Ratings Migration | CreditMetrics | Simulates rating *migrations*, not just default, and revalues on the new curve |
| Basel Single-Factor Capital | Regulatory (ASRF) | Closed-form portfolio capital under Basel's infinitely-granular-portfolio assumption |

Full derivations are in `docs/`.

## Getting started

```bash
git clone <your-repo-url>
cd credit-risk-toolkit
pip install -r requirements.txt

# run the dashboard
streamlit run app.py

# or use a model directly in Python / a notebook
python -c "
from credit_risk import merton, sample_data
result = merton.calibrate_merton(**sample_data.MERTON_SAMPLE)
print(result.pd_table())
"
```

Every module also runs standalone for a quick smoke test:
`python -m credit_risk.kmv_montecarlo`, etc.

## Known limitations (read before using for anything real)

- **Correlation convention split** — see
  [docs/06_correlation_conventions.md](docs/06_correlation_conventions.md).
- **Term-structure PD calibration is under-identified** — fitting a PD
  per period against one market price has many equally-good solutions;
  see [docs/01_bond_implied_pd.md](docs/01_bond_implied_pd.md).
- **Multi-year positions in the ratings-migration model** re-use the
  1-year transition matrix as an approximation rather than the correct
  $T^N$ matrix power; see
  [docs/04_credit_var_ratings.md](docs/04_credit_var_ratings.md).
- **All rate/spread curves in `sample_data.py` are hypothetical**
  (per the original author), not live market data — swap in real quotes
  before drawing real conclusions.
- None of this is investment, credit, or regulatory advice — it's a
  learning/portfolio project implementing textbook credit-risk models.

## License

Add a license of your choice (MIT is a common default for a portfolio
project like this) before publishing.
