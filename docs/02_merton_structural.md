# 2. Merton Structural Model (`credit_risk/merton.py`)

**Core idea (Merton, 1974).** A levered firm's equity is economically a
call option on the firm's assets, struck at the face value of debt: at
maturity, shareholders get $\max(V_T - D, 0)$ — they walk away
(default) if assets are worth less than the debt owed, otherwise they
keep the residual.

## The two equations

Under Black-Scholes-Merton assumptions (assets follow GBM, debt is a
single zero-coupon claim maturing at $T$), equity value is:

$$
S = V\,N(d_1) - D e^{-rT} N(d_2)
$$

$$
d_1 = \frac{\ln(V/D) + \left(r + \tfrac12 \sigma_V^2\right)T}{\sigma_V\sqrt{T}},
\qquad d_2 = d_1 - \sigma_V\sqrt{T}
$$

By Itô's lemma applied to $S = S(V)$, equity volatility relates to asset
volatility via the option's delta:

$$
\sigma_E S = N(d_1)\,\sigma_V V
$$

## Why calibration is needed

$V$ (firm asset value) and $\sigma_V$ (asset volatility) are **not
observable** — only equity value $S$ and equity volatility $\sigma_E$
are (from the stock market). So we have 2 equations and 2 unknowns
$(V, \sigma_V)$, solved jointly by minimizing:

$$
\text{SSE}(V,\sigma_V) = \big(S - \text{Call}(V,\sigma_V)\big)^2
+ \lambda\big(\sigma_E - \hat\sigma_E(V,\sigma_V)\big)^2
$$

(the $\lambda = 10^6$ weight in the code balances the very different
scales of a price-error term vs. a volatility-error term — without it,
the optimizer would effectively ignore the volatility equation).

## Default probability

Once calibrated, the risk-neutral probability the firm defaults by $T$
(assets end up below the debt) is:

$$
PD = \Pr(V_T < D) = N(-d_2)
$$

This is a **risk-neutral** PD (compensates for both true default risk
*and* the market price of that risk), not a real-world / "physical" PD
— real-world PD would require an estimate of the asset's actual expected
return (drift), not just $r$.

## A practical calibration note

`calibrate_merton` seeds the optimizer at $V_0 = S + D$ (equity + debt),
not $V_0 = S$ alone. A firm's asset value must be at least as large as
its equity value, since assets also have to cover the debt — starting
the search at $S$ can bias Nelder-Mead toward a poor local optimum for
highly levered firms. This is a genuine improvement over the original
script, not just a style change — verify convergence (`SSE` near 0) on
your own data.

## Relationship to KMV

`kmv_montecarlo.py` extends this same Merton machinery to a *portfolio*
via Monte Carlo: instead of solving the option-implied $V$ from market
prices for the whole book, it directly simulates each firm's asset value
at the horizon and checks whether it fell below its debt/default point,
with firms correlated through a shared market factor. See
[06_correlation_conventions.md](06_correlation_conventions.md) for the
correlation-parameterization detail that matters when moving from this
single-firm model to the portfolio version.
