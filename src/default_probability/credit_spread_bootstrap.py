# -*- coding: utf-8 -*-
"""
Model-free bootstrap of implied survival/default probabilities directly
from a term structure of credit spreads: compare each period's risky
zero-coupon bond price to the equivalent risk-free price to back out
cumulative survival probability, then difference across periods to get
unconditional (marginal) and conditional (hazard-rate style) PDs.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd


def analyze_credit_risk(
    risk_free_rates: Sequence[float],
    risky_rates: Sequence[float],
    recovery_rate: float = 0.0,
) -> pd.DataFrame:
    rf = np.asarray(risk_free_rates, dtype=float)
    r = np.asarray(risky_rates, dtype=float)
    if len(rf) != len(r):
        raise ValueError(f"Length mismatch: rf ({len(rf)}) and r ({len(r)}) must match.")

    n = len(rf)
    periods = np.arange(1, n + 1)

    discount_rf = 1 / (1 + rf) ** periods
    discount_r = 1 / (1 + r) ** periods
    price_riskless = 100 * discount_rf
    price_risky = 100 * discount_r
    spread = r - rf

    if recovery_rate == 0.0:
        cum_survival = price_risky / price_riskless
    else:
        cum_survival = (price_risky / price_riskless - recovery_rate) / (1 - recovery_rate)
        cum_survival = np.clip(cum_survival, 0, 1)

    cum_default = 1 - cum_survival

    unconditional_pd = np.empty(n)
    unconditional_pd[0] = cum_default[0]
    unconditional_pd[1:] = np.diff(cum_default)

    conditional_pd = np.empty(n)
    conditional_pd[0] = unconditional_pd[0]
    conditional_pd[1:] = unconditional_pd[1:] / cum_survival[:-1]

    return pd.DataFrame({
        "Period (t)": periods,
        "Risk-Free Rate": [f"{x:.4%}" for x in rf],
        "Risky Rate": [f"{x:.4%}" for x in r],
        "Credit Spread": [f"{x:.4%}" for x in spread],
        "Price Riskless": np.round(price_riskless, 2),
        "Price Risky": np.round(price_risky, 2),
        "Cum. Survival Prob.": [f"{x:.2%}" for x in cum_survival],
        "Cum. Default Prob.": [f"{x:.2%}" for x in cum_default],
        "Unconditional PD": [f"{x:.2%}" for x in unconditional_pd],
        "Conditional PD": [f"{x:.2%}" for x in conditional_pd],
    }).set_index("Period (t)")
