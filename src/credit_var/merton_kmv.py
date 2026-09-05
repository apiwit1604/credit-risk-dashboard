# -*- coding: utf-8 -*-
"""
Merton / KMV-style single-factor asset-value Monte Carlo model for
portfolio Credit VaR.

Each firm's log-asset-return is driven by a common systematic factor plus
an idiosyncratic shock (a one-factor Gaussian copula: `asset_correlation`
is each firm's R^2 loading on the common factor). A firm defaults in the
simulation whenever its simulated terminal asset value falls below its
EAD, used here as a simplified default barrier in place of a full debt
schedule.
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
import pandas as pd


def run_kmv_simulation(
    portfolio: Sequence[dict],
    loss_horizon: float,
    n_sims: int,
    confidence_level: float = 0.99,
    random_seed: Optional[int] = 42,
) -> dict:
    rng = np.random.default_rng(random_seed)
    n_firms = len(portfolio)

    market_shock = rng.standard_normal(n_sims)
    firm_losses = np.zeros((n_firms, n_sims))
    default_matrix = np.zeros((n_firms, n_sims), dtype=bool)

    for i, firm in enumerate(portfolio):
        z_firm = rng.standard_normal(n_sims)
        rho = np.sqrt(firm["asset_correlation"])
        combined_z = rho * market_shock + np.sqrt(1 - firm["asset_correlation"]) * z_firm

        returns = firm["asset_mean"] + firm["asset_std"] * combined_z
        asset_at_maturity = firm["asset_value"] * np.exp(loss_horizon * returns)

        default_matrix[i] = asset_at_maturity < firm["ead"]
        firm_losses[i] = np.where(default_matrix[i], firm["ead"] * firm["lgd"], 0.0)

    total_loss = firm_losses.sum(axis=0)

    expected_loss = float(total_loss.mean())
    var = float(np.percentile(total_loss, confidence_level * 100))
    expected_shortfall = float(total_loss[total_loss >= var].mean())
    economic_capital = var - expected_loss

    pd_series = default_matrix.mean(axis=1)
    pd_df = pd.DataFrame({
        "Firm Name": [f["name"] for f in portfolio],
        "Probability of Default (PD)": pd_series,
    })

    # --- Bug fix vs. the original notebook ------------------------------
    # The function's own parameter is `n_sims`, but the event-summary table
    # was built using the *global* `n_sim` variable instead. That was
    # invisible in the notebook only because every call happened to pass
    # the same value as the global — an assumption a dashboard slider
    # breaks immediately. The `n_sims` below is the local parameter,
    # consistently, everywhere.
    #
    # --- Performance fix vs. the original notebook ----------------------
    # The original built this table with a pure-Python loop over every
    # single simulation draw (`for i in range(n_sim)`), which is fine at
    # notebook-run-once speed but turns a slider drag into a multi-second
    # freeze in an interactive dashboard. Bit-packing each firm's
    # default/solvent outcome into one integer code and using
    # `np.unique` is the vectorized equivalent: the only Python-level loop
    # left is over the (small) number of *distinct* joint scenarios that
    # actually occurred, not over every simulation draw.
    codes = np.zeros(n_sims, dtype=np.int64)
    for i in range(n_firms):
        codes |= default_matrix[i].astype(np.int64) << i

    unique_codes, inverse, counts = np.unique(codes, return_inverse=True, return_counts=True)
    avg_loss_by_code = np.zeros(len(unique_codes))
    np.add.at(avg_loss_by_code, inverse, total_loss)
    avg_loss_by_code /= counts

    event_labels = [
        tuple("D" if (code >> i) & 1 else "S" for i in range(n_firms))
        for code in unique_codes
    ]

    event_summary = pd.DataFrame({
        "Event (F1, F2, ...)": event_labels,
        "Occur": counts,
        "Loss Event": avg_loss_by_code,
        "PB": counts / n_sims,
    })

    return {
        "total_loss": total_loss,
        "pd": pd_df,
        "event_summary": event_summary,
        "default_matrix": default_matrix,
        "expected_loss": expected_loss,
        "var": var,
        "expected_shortfall": expected_shortfall,
        "economic_capital": economic_capital,
    }
