# 5. Basel Single-Factor (IRB / ASRF) Capital (`credit_risk/basel_single_factor.py`)

The regulatory closed-form counterpart to the Monte Carlo models above —
this is (a version of) the actual formula banks use under Basel II/III
Internal Ratings-Based (IRB) approach to compute minimum regulatory
capital, **without** needing to simulate a portfolio at all.

## Where the closed form comes from

Basel's formula is the single-factor Vasicek/Merton model
(same $Z_i = \sqrt{R}M + \sqrt{1-R}\varepsilon_i$ structure as
`kmv_montecarlo.py`) taken to the limit of an **infinitely granular**
portfolio (Asymptotic Single Risk Factor, ASRF): as the number of
independent, small exposures grows, idiosyncratic risk diversifies away
completely, and only the systematic (market-factor) component of loss
remains uncertain. In that limit, the loss distribution's $\alpha$-th
percentile has a closed-form expression — no simulation needed.

## The formula

**Step 1 — Asset correlation** (Basel's prescribed formula for corporate
exposures, a function of PD alone):

$$
R(PD) = 0.12\cdot w + 0.24\cdot(1-w), \qquad
w = \frac{1-e^{-50\,PD}}{1-e^{-50}}
$$

Note the shape: **lower-PD (higher-quality) obligors get a *higher*
asset correlation** — the intuition is that safer firms tend to default
only when broad economic conditions turn bad (systematic risk
dominates), while riskier firms are more likely to fail for
idiosyncratic, firm-specific reasons.

**Step 2 — Worst-case default rate** at confidence level $\alpha$ (Basel
fixes $\alpha = 99.9\%$):

$$
WCDR = \Phi\!\left[
\frac{\Phi^{-1}(PD)}{\sqrt{1-R}} + \sqrt{\frac{R}{1-R}}\;\Phi^{-1}(\alpha)
\right]
$$

This is the conditional PD in the $\alpha$-quantile-worst realization of
the systematic factor $M$ — i.e. "if the economy is as bad as it gets
once every 1-in-1000 years, what fraction of this obligor class
defaults?"

**Step 3 — Capital requirement** (as a fraction of EAD):

$$
K = LGD \times WCDR - LGD \times PD
$$

The second term backs out Expected Loss, because — per Basel's own
framework — capital is meant to cover *unexpected* loss only; EL is
assumed to be covered separately (through provisioning/pricing).

**Step 4 — Dollar capital and portfolio aggregation:**

$$
\text{Capital}_i = K_i \times EAD_i, \qquad
\text{Expected Loss}_i = PD_i \times LGD_i \times EAD_i
$$

Because of the ASRF assumption, portfolio-level capital is simply the
**sum** across obligors — no correlation/aggregation step is needed at
the portfolio level (the correlation is already baked into each $R_i$).
This additivity is the single biggest simplification versus the
Monte Carlo models in this repo, and it's worth being explicit about
with anyone reading the dashboard: Basel IRB capital assumes the bank's
book is large and granular enough that firm-specific risk has
diversified away. For a small, concentrated portfolio (like the 2- or
3-firm toy examples used elsewhere in this repo), that assumption
clearly does *not* hold — which is exactly why the Monte Carlo models
(KMV, ratings-migration Credit VaR) exist: they capture the
concentration risk that Basel's closed form assumes away.

## Bug fixed here

The original script defined `get_single_factor_BIS(...)` and a
`PORTFOLIO` list, but the code that was supposed to loop over
`PORTFOLIO`, call the function per firm, and build `df_portfolio` was
missing — the script referenced `df_portfolio` without ever defining it,
which would raise `NameError` if run as-is. `run_portfolio_capital()`
in the cleaned module is the completed version of that missing loop.
