# -*- coding: utf-8 -*-
"""
KMV / Merton Structural Model — Monte Carlo Credit VaR
========================================================

Simulates firm asset values under Geometric Brownian Motion (Merton /
KMV structural credit risk framework), with a single systematic market
factor driving correlated defaults across the portfolio (Vasicek-style
single-factor copula on the asset returns).

A firm defaults in a given simulation path if its simulated asset value
at maturity falls below its debt (face value of liabilities) — the
classic Merton "distance to default" trigger.

This is a MONTE CARLO model — the confidence level (alpha) is applied as
an empirical percentile over simulated portfolio losses, so it can be
freely changed and compared against other Monte Carlo models (e.g. the
CreditMetrics model in this repo) at the same alpha. It is NOT directly
comparable to the BIS/Basel closed-form model without care — see the
repo root README.
"""

import numpy as np
import pandas as pd

# Portfolio configuration: one entry per firm.
#   asset                : current market value of firm assets
#   debt                 : face value of debt (default threshold at maturity)
#   mean                 : expected annual asset return (drift), decimal
#   standard_deviation   : annual asset volatility, decimal
#   lgd                  : loss given default, decimal fraction of debt
#   asset_correlation    : firm's correlation to the single market factor
PORTFOLIO = [
    {
        "name": "Firm_1",
        "asset": 100_000,
        "debt": 120_000,
        "mean": 0.10,
        "standard_deviation": 0.30,
        "lgd": 0.30,
        "asset_correlation": 0.23,
    },
    {
        "name": "Firm_2",
        "asset": 150_000,
        "debt": 120_000,
        "mean": 0.19,
        "standard_deviation": 0.35,
        "lgd": 0.21,
        "asset_correlation": 0.70,
    },
    {
        "name": "Firm_3",
        "asset": 180_000,
        "debt": 120_000,
        "mean": 0.75,
        "standard_deviation": 0.80,
        "lgd": 0.15,
        "asset_correlation": 0.10,
    },
]

N_SIMULATIONS = 1_000_000  # Monte Carlo paths

# NOTE ON ALPHA: this is the model-level default only. To compare against
# CreditMetrics_Model at the SAME confidence level, pass the same
# `confidence_level` argument to both models' run functions rather than
# editing this constant — see notebooks/Credit_VaR_Models_Comparison.ipynb.
DEFAULT_CONFIDENCE_LEVEL = 0.999


def run_kmv_simulation(portfolio, n_sims, confidence_level=0.99):
    
    """
    Run a Monte Carlo KMV/Merton simulation across the portfolio.

    Parameters
    ----------
    portfolio : list[dict]
        List of firm dicts as defined in PORTFOLIO above.
    n_sims : int
        Number of Monte Carlo simulation paths.
    confidence_level : float
        Alpha for VaR / CVaR, e.g. 0.99 for 99%, 0.999 for 99.9%.
        Defaults to 0.999 to align with the BIS model's fixed regulatory
        standard, but is fully adjustable here since this is simulation-based.

    Returns
    -------
    total_loss : np.ndarray, shape (n_sims,)
        Total portfolio loss per simulation path.
    default_matrix : np.ndarray[bool], shape (n_firms, n_sims)
        Default indicator per firm per simulation.
    p_var : float
        Portfolio Credit VaR at `confidence_level` (loss percentile).
    p_cvar : float
        Portfolio CVaR / Expected Shortfall — mean loss in the tail
        beyond VaR.
    expected_loss : float
        The average loss you expect on an ordinary day. 
        This is considered a predictable cost of doing business.
    economic_capital : float
        The extra cash cushion you must set aside to keep your organization 
        solvent during an extreme crisis. It is calculated as
        ec = cvar - el

    """

    n_firms = len(portfolio)
    market_shock = np.random.standard_normal(n_sims)
    firm_losses = np.zeros((n_firms, n_sims))
    default_matrix = np.zeros((n_firms, n_sims), dtype=bool)

    for i, firm in enumerate(portfolio):
        # 1. สร้างความสัมพันธ์ผ่าน Market Factor
        z_firm = np.random.standard_normal(n_sims)
        rho = np.sqrt(firm['asset_correlation'])
        combined_z = (rho * market_shock) + (np.sqrt(1 - firm['asset_correlation']) * z_firm)

        # 2. คำนวณ Asset Value (KMV Model)
        drift = (firm['mean'] - 0.5 * firm['standard_deviation']**2)
        diffusion = firm['standard_deviation'] * combined_z
        asset_at_maturity = firm['asset'] * np.exp(drift + diffusion)

        # 3. ระบุสถานะ Default และ Loss
        default_matrix[i] = asset_at_maturity < firm['debt']
        firm_losses[i] = np.where(default_matrix[i], firm['debt'] * firm['lgd'], 0)

    total_loss = np.sum(firm_losses, axis=0)

    # คำนวณ Metrics
    expected_loss = total_loss.mean()
    p_var = np.percentile(total_loss, confidence_level * 100)
    p_cvar = total_loss[total_loss >= p_var].mean()
    economic_capital = p_var - expected_loss

    return {
        'total_loss': total_loss,
        'default_matrix': default_matrix,
        'expected_loss': expected_loss,
        'p_var': p_var,
        'p_cvar': p_cvar,
        'economic_capital': economic_capital
    }


def get_scenario_summary(portfolio, default_matrix, losses):
    """
    Build a Survive/Default scenario table: every combination of firm
    outcomes observed in the simulation, its empirical probability, and
    average loss.
    """
    n_sims = default_matrix.shape[1]
    n_firms = len(portfolio)

    scenario_strings = [
        "(" + ",".join("D" if default_matrix[i, j] else "S" for i in range(n_firms)) + ")"
        for j in range(n_sims)
    ]

    df_sims = pd.DataFrame({"Scenario": scenario_strings, "Loss": losses})

    summary = (
        df_sims.groupby("Scenario")
        .agg(Occurrences=("Loss", "count"), Avg_Loss=("Loss", "mean"))
        .reset_index()
    )
    summary["Probability"] = summary["Occurrences"] / n_sims
    summary = summary.drop(columns=["Occurrences"])
    summary = summary.sort_values("Avg_Loss", ascending=True)
    summary["Cumulative_Prob"] = summary["Probability"].cumsum()

    return summary


if __name__ == "__main__":
    results = run_kmv_simulation(PORTFOLIO, N_SIMULATIONS, DEFAULT_CONFIDENCE_LEVEL)

    losses = results['total_loss']
    def_matrix = results['default_matrix']

    print(f"Expected Loss: {results['expected_loss']:,.2f}")
    print(f"Portfolio Credit VaR ({DEFAULT_CONFIDENCE_LEVEL*100}%): {results['p_var']:,.2f}")
    print(f"Economic Capital: {results['economic_capital']:,.2f}")
    print(f"Portfolio CVaR (Expected Shortfall): {results['p_cvar']:,.2f}")

    scenario_table = get_scenario_summary(PORTFOLIO, def_matrix, losses)
    print("\nScenario summary (head):")
    print(scenario_table.head(10).to_string(index=False))
