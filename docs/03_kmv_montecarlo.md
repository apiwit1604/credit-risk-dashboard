# 3. KMV Portfolio Monte Carlo (`credit_risk/kmv_montecarlo.py`)

Extends the single-firm Merton model (see
[02_merton_structural.md](02_merton_structural.md)) to a **portfolio**,
via simulation instead of a closed-form option formula — because once
firms are correlated with each other, the portfolio loss distribution
generally has no closed form.

## Single-factor asset model

Every firm's asset return is driven partly by a common market factor $M$
and partly by its own idiosyncratic shock:

$$
Z_i = \sqrt{R_i}\, M + \sqrt{1-R_i}\, \varepsilon_i,
\qquad M,\varepsilon_i \stackrel{iid}{\sim} N(0,1)
$$

$R_i$ is this model's `asset_correlation` parameter — see
[06_correlation_conventions.md](06_correlation_conventions.md) for
**why this is a different convention from `credit_var_ratings.py`**,
which is important if you ever want to feed "the same" correlation
number into both models.

## Simulating the firm's asset value

Each firm's asset value at the horizon follows a lognormal GBM driven by
$Z_i$:

$$
V_{i,T} = V_{i,0}\, \exp\!\Big[\big(\mu_i - \tfrac12\sigma_i^2\big)T +
\sigma_i \sqrt{T}\, Z_i\Big]
$$

Default is triggered when $V_{i,T}$ falls below the firm's debt (its
KMV "default point"):

$$
\text{Default}_i \iff V_{i,T} < D_i
$$

and the loss on that path is $D_i \times \text{LGD}_i$ (a fixed
fraction of debt face value — a simplification; a fuller model would
also let recovery vary stochastically).

## Portfolio metrics

Across $N$ simulated paths, the portfolio loss $L^{(s)} = \sum_i
\text{Loss}_i^{(s)}$ gives an empirical loss distribution, from which:

$$
\text{Expected Loss (EL)} = \frac{1}{N}\sum_s L^{(s)}
$$

$$
\text{VaR}_\alpha = \inf\{\ell : \Pr(L \le \ell) \ge \alpha\}
\quad \text{(the $\alpha$-th percentile of simulated loss)}
$$

$$
\text{CVaR}_\alpha = \mathbb{E}[L \mid L \ge \text{VaR}_\alpha]
\quad\text{(mean loss in the tail beyond VaR — a.k.a. Expected Shortfall)}
$$

$$
\text{Economic Capital} = \text{VaR}_\alpha - \text{EL}
$$

Economic Capital is the standard regulatory-capital logic: EL is treated
as a predictable cost of business (covered by pricing/provisions), while
the *unexpected* loss beyond EL, up to the chosen confidence level, is
what capital needs to cushion.

## Convergence note

VaR/CVaR at very high confidence (e.g. 99.9%) are tail statistics — they
are noisy with too few simulations, especially for small portfolios like
the 3-firm example here where the tail is dominated by a handful of
joint-default paths. Increase `n_sims` and check that VaR/CVaR stabilize
before trusting the numbers for a real capital decision.
