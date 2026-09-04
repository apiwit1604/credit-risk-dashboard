# 6. ⚠️ Correlation Conventions — Read This Before Comparing Models

This toolkit contains **two different, incompatible conventions** for
what "asset correlation" means in a single-factor credit model. Both are
legitimate conventions used in industry — the problem is only that this
project uses both, under the same field name, in different files. If you
carry a correlation number from one model into another without
converting it, your results will be silently wrong.

## Convention A — plain correlation coefficient ("rho")

Used in: **`credit_var_ratings.py`**

$$
Z_i = \rho_i M + \sqrt{1-\rho_i^2}\,\varepsilon_i
$$

Here `asset_correlation` **is** $\rho_i = \text{Corr}(Z_i, M)$ directly.
Sample values in this repo: 0.15, 0.20 (moderate, plausible correlation
coefficients).

## Convention B — "R" = variance explained by the market (rho²)

Used in: **`kmv_montecarlo.py`** and **`basel_single_factor.py`**
(this is also literally how Basel's own IRB documentation defines its
asset-correlation parameter):

$$
Z_i = \sqrt{R_i}\, M + \sqrt{1-R_i}\,\varepsilon_i
$$

Here `asset_correlation` **is** $R_i = \rho_i^2$. So a `kmv_montecarlo.py`
input of `asset_correlation = 0.70` implies an *actual* correlation
coefficient of $\rho = \sqrt{0.70} \approx 0.84$ — an extremely high
correlation with the market that would be unusual for a real corporate
name. (Contrast with Firm_2 in the KMV sample portfolio, which by
convention A would only imply $\rho=0.70$, itself already high.)

## Why this matters in practice

| If your `asset_correlation` input is intended as... | and you feed it into `kmv_montecarlo.py` (Convention B) | and you feed it into `credit_var_ratings.py` (Convention A) |
|---|---|---|
| $\rho = 0.20$ (a correlation coefficient) | Wrong — model reads it as $R=0.20 \Rightarrow \rho \approx 0.45$, over 2x too high | Correct |
| $R = 0.20$ (variance explained) | Correct | Wrong — model reads it as $\rho=0.20 \Rightarrow R = 0.04$, 5x too low |

The error compounds silently — there's no crash, no obviously wrong
output, just a wrong-by-a-multiple correlation baked into every VaR/CVaR
number downstream.

## Recommendation

This repo has **not** silently unified the two — the original math in
each file has been preserved, because it isn't possible to know from
the outside which convention the *specific numbers* you originally
chose (0.15, 0.20, 0.23, 0.70, 0.10) were meant under. That decision is
yours to make with your own data provenance in mind.

If/when you do standardize, the recommendation is to converge on
**Convention B (Basel-R)**, because:
1. Two of the three correlation-sensitive models (`kmv_montecarlo.py`,
   `basel_single_factor.py`) already use it.
2. It matches the Basel IRB formula you've already correctly
   implemented, so the whole toolkit would use one mental model of
   "asset correlation" consistent with actual regulatory usage.
3. To convert a Convention-A number to Convention B: $R = \rho^2$.

If you standardize, the only code change needed is in
`credit_var_ratings.simulate_rating_outcomes`: replace

```python
z = rho * market_factor + np.sqrt(1 - rho ** 2) * idiosyncratic
```

with

```python
z = np.sqrt(rho) * market_factor + np.sqrt(1 - rho) * idiosyncratic
```

(and rename the variable / field to `R` to make the convention
unambiguous going forward) — but note this will change every
downstream VaR/CVaR number from that model, so re-validate before
relying on it.
