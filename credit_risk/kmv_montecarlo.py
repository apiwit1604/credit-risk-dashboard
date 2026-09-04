"""
kmv_montecarlo.py
==================
Monte Carlo portfolio credit-risk engine built on the Merton/KMV
single-factor asset model. Each firm's (log) asset return over the
horizon is driven by a common market factor M and an idiosyncratic
shock, correlated to the market through the firm's asset correlation.

Model idea (single-factor asset model, "Basel-R" convention)
--------------------------------------------------------------
For each firm i, define the standardized combined shock

    Z_i = sqrt(R_i) * M + sqrt(1 - R_i) * eps_i,      M, eps_i ~ iid N(0,1)

so that Corr(Z_i, M) = sqrt(R_i). R_i is what this codebase calls
`asset_correlation`.

>>> CONVENTION WARNING <<<
This R_i is the SAME parameterization used in basel_single_factor.py
(Basel calls it "asset correlation" even though it is really the
variance-of-returns explained by the market factor, i.e. what a
statistician would call rho^2, not rho). It is a DIFFERENT convention
from credit_var_ratings.py, which uses its `asset_correlation` as a
plain correlation coefficient rho directly (Z = rho*M + sqrt(1-rho^2)*eps).
Do not plug a number calibrated for one model into the other without
converting (R = rho^2). See docs/06_correlation_conventions.md.

The firm's asset value at the horizon is simulated as a lognormal GBM
driven by Z_i:

    V_T = V_0 * exp[ (mu - 0.5 sigma^2) T + sigma sqrt(T) Z_i ]

(T = 1 year, matching the source model.) Default occurs when V_T falls
below the firm's debt (the KMV default point); loss given default is
Debt * LGD.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class KMVPortfolioResult:
    total_loss: np.ndarray      # shape (n_sims,)
    default_matrix: np.ndarray  # shape (n_firms, n_sims), bool
    expected_loss: float
    var: float
    cvar: float
    economic_capital: float


def run_kmv_portfolio_simulation(portfolio, n_sims: int = 100_000, confidence_level: float = 0.999,
                                  random_seed: int | None = None) -> KMVPortfolioResult:
    """
    portfolio: list of dicts, each with keys:
        name, asset (V0), debt (default point), mean (mu),
        standard_deviation (sigma), lgd, asset_correlation (R_i -- see
        the Basel-R convention warning in the module docstring)
    """
    rng = np.random.default_rng(random_seed)
    n_firms = len(portfolio)

    market_shock = rng.standard_normal(n_sims)
    firm_losses = np.zeros((n_firms, n_sims))
    default_matrix = np.zeros((n_firms, n_sims), dtype=bool)

    for i, firm in enumerate(portfolio):
        R = firm["asset_correlation"]
        idiosyncratic_shock = rng.standard_normal(n_sims)
        z = np.sqrt(R) * market_shock + np.sqrt(1 - R) * idiosyncratic_shock

        drift = firm["mean"] - 0.5 * firm["standard_deviation"] ** 2
        diffusion = firm["standard_deviation"] * z
        asset_at_horizon = firm["asset"] * np.exp(drift + diffusion)

        default_matrix[i] = asset_at_horizon < firm["debt"]
        firm_losses[i] = np.where(default_matrix[i], firm["debt"] * firm["lgd"], 0.0)

    total_loss = firm_losses.sum(axis=0)
    expected_loss = float(total_loss.mean())
    var = float(np.percentile(total_loss, confidence_level * 100))
    cvar = float(total_loss[total_loss >= var].mean())
    economic_capital = var - expected_loss

    return KMVPortfolioResult(
        total_loss=total_loss, default_matrix=default_matrix,
        expected_loss=expected_loss, var=var, cvar=cvar, economic_capital=economic_capital,
    )


if __name__ == "__main__":
    portfolio = [
        {"name": "Firm_1", "asset": 100_000, "debt": 120_000, "mean": 0.10,
         "standard_deviation": 0.30, "lgd": 0.30, "asset_correlation": 0.23},
        {"name": "Firm_2", "asset": 150_000, "debt": 120_000, "mean": 0.19,
         "standard_deviation": 0.35, "lgd": 0.21, "asset_correlation": 0.70},
        {"name": "Firm_3", "asset": 180_000, "debt": 120_000, "mean": 0.75,
         "standard_deviation": 0.80, "lgd": 0.15, "asset_correlation": 0.10},
    ]
    result = run_kmv_portfolio_simulation(portfolio, n_sims=200_000, confidence_level=0.999, random_seed=42)
    print(f"Expected Loss: {result.expected_loss:,.2f}")
    print(f"VaR(99.9%):    {result.var:,.2f}")
    print(f"CVaR(99.9%):   {result.cvar:,.2f}")
    print(f"Econ. Capital: {result.economic_capital:,.2f}")
