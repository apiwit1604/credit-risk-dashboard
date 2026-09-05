# -*- coding: utf-8 -*-
"""
Merton (1974) structural / option-theoretic model: firm equity is treated
as a European call option on the firm's assets (Black-Scholes). Asset
value and asset volatility are solved for jointly so the model reproduces
the observed equity value and equity volatility. The resulting distance-
to-default gives a *risk-neutral* probability of default — it uses the
risk-free rate as drift, not the firm's real-world expected asset return
(see the README for why that distinction matters).
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm


def merton_model(
    equity_value: float,
    debt_face_value: float,
    equity_vol: float,
    risk_free_rate: float,
    maturity: float = 1.0,
    weight_sigma: float = 1e6,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Parameters
    ----------
    equity_value : market value of equity (S)
    debt_face_value : face value of debt (D)
    equity_vol : annualised equity volatility (sigma)
    risk_free_rate : annualised risk-free rate (r)
    maturity : time to debt maturity in years (T)
    weight_sigma : penalty weight on the volatility-matching equation inside
        the joint SSE minimization. Known simplification — see the
        "Limitations" section of the README: solving the exact 2-equation
        system (e.g. via `scipy.optimize.fsolve`) is the more standard
        approach; this weighted single-objective heuristic depends on
        `weight_sigma` and the optimizer's convergence.

    Returns
    -------
    (summary_df, pd_df) : optimal firm value / asset vol / SSE, and the
    risk-neutral probability of default.
    """
    S, D, sigma, r, T = equity_value, debt_face_value, equity_vol, risk_free_rate, maturity

    def sse(params):
        V, sigma_v = params
        if V <= 0 or sigma_v <= 0:
            return 1e10
        d1 = (np.log(V / D) + (r + 0.5 * sigma_v ** 2) * T) / (sigma_v * np.sqrt(T))
        d2 = d1 - sigma_v * np.sqrt(T)
        call_on_fv = V * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)
        sigma_call_on_fv = norm.cdf(d1) * sigma_v * V / S
        return (S - call_on_fv) ** 2 + weight_sigma * (sigma - sigma_call_on_fv) ** 2

    x0 = [S + D, sigma * (S / (S + D))]
    result = minimize(sse, x0, method="Nelder-Mead")
    v_opt, sigma_v_opt = result.x

    d1 = (np.log(v_opt / D) + (r + 0.5 * sigma_v_opt ** 2) * T) / (sigma_v_opt * np.sqrt(T))
    d2 = d1 - sigma_v_opt * np.sqrt(T)
    call_on_fv = v_opt * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)
    pd_risk_neutral = 1 - norm.cdf(d2)

    summary_df = pd.DataFrame(
        {"Value": [v_opt, sigma_v_opt, call_on_fv, result.fun]},
        index=["Optimal Firm Value", "Optimal Asset Vol (sigma_V)", "Call on Firm Value (= S)", "SSE"],
    )
    summary_df.index.name = "Parameter"

    pd_df = pd.DataFrame({"Value": [pd_risk_neutral]}, index=["Risk-Neutral PD"])
    pd_df.index.name = "Probability of Default"
    return summary_df, pd_df
