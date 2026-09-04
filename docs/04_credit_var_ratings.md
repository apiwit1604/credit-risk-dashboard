# 4. Credit VaR — Ratings Migration (`credit_risk/credit_var_ratings.py`)

A CreditMetrics-style portfolio Credit VaR model: instead of a binary
default/no-default outcome (as in KMV), each position can migrate to
*any* credit rating, and its value changes accordingly — capturing
"downgrade risk", not just default risk.

## Step 1 — Systematic risk factor

Same single-factor structure as KMV, but in the **plain-rho**
convention (see [06_correlation_conventions.md](06_correlation_conventions.md)
for why this differs from `kmv_montecarlo.py`):

$$
Z_i = \rho_i M + \sqrt{1-\rho_i^2}\,\varepsilon_i
$$

## Step 2 — Mapping $Z_i$ to a rating (threshold model)

Take firm $i$'s row of the 1-year transition matrix — the probability of
migrating from its current rating to every other rating, including
default. Turn cumulative probabilities into thresholds on the standard
normal axis via the inverse CDF:

$$
z_{\text{threshold},k} = \Phi^{-1}\!\left(\sum_{j\le k} p_j\right)
$$

Then firm $i$'s simulated rating in a given path is whichever bucket
$Z_i$ falls into. This is the standard CreditMetrics technique — it
reproduces the *marginal* transition probabilities exactly by
construction, while correlating outcomes across firms through the
shared $M$.

## Step 3 — Revaluation at the new rating

For every simulated *joint* scenario (one rating outcome per firm), each
position is revalued as if the market now prices it off its **new**
rating's credit curve:

$$
\text{Loss}_i = \text{Value}_i(\text{original rating}) -
\text{Value}_i(\text{simulated rating})
$$

where $\text{Value}_i(\cdot)$ discounts the position's remaining cash
flows on the corporate spot curve for that rating (built by cubic-spline
interpolation across the rating's spread curve — see
`_forward_rate` in the code). If the simulated outcome is default, value
collapses to $EAD \times (1-\text{LGD})$.

## Step 4 — Aggregate to VaR / ES / EC

Same definitions as in [03_kmv_montecarlo.md](03_kmv_montecarlo.md), but
built from the *exact* scenario probabilities (since the joint outcome
space here is discrete and enumerable) rather than a raw empirical
percentile — the code sorts scenarios by loss and walks the cumulative
probability up to $\alpha$.

## ⚠️ Known limitation — multi-year positions

`rating_transition_probabilities` re-uses the **1-year** transition
matrix directly, even for a position with `years_to_maturity > 1` (e.g.
the sample portfolio's Firm_2, a 2-year BB bond). This treats "the
1-year-ahead migration probability" as if it were "the 2-year-ahead
migration probability", which is only an approximation — it ignores the
fact that a firm could migrate more than once over 2 years (e.g.
BB→BBB→A).

The mathematically correct fix is the **N-th matrix power** of the
transition matrix:

$$
T^{(N)} = T^N
$$

`transition_matrix_power()` is provided in the module (via
`scipy.linalg.fractional_matrix_power`, which also supports fractional
horizons like 0.5 years) but is **not yet wired into the simulation** —
this is a concrete next step before trusting multi-year portfolio
results, and is exactly the kind of gap that's easy to miss when a
demo/prototype quietly becomes production code.

## Data-entry bug fixed in the sample data

The original source had Firm_2 configured with `payments_per_year = 9`
next to a comment saying "pays annually" — annually should be `1`. This
has been corrected in `sample_data.CREDIT_VAR_PORTFOLIO`. With the bug
in place, the model was pricing Firm_2 as if it made 9 coupon payments
per year, which would have materially distorted both its standalone
valuation and its contribution to portfolio loss. **Double check this
wasn't intentional (e.g. some other payment frequency) before relying on
the corrected version.**
