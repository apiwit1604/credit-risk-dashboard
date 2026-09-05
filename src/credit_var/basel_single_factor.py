# -*- coding: utf-8 -*-
"""
Basel II/III Asymptotic Single Risk Factor (ASRF) formula for portfolio
Credit VaR — an analytical, closed-form counterpart to the two Monte Carlo
models, using the regulatory corporate-exposure correlation and maturity
adjustment formulas at the fixed 99.9% confidence level required by the
Basel IRB framework.
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
import pandas as pd
from scipy.stats import norm

BASEL_CONFIDENCE: float = 0.999


def run_single_factor_basel(
    portfolio: Sequence[dict],
    transition_matrix_n: pd.DataFrame,
    maturity_override: Optional[float] = None,
) -> dict:
    """
    Parameters
    ----------
    maturity_override:
        If given, use this effective maturity M for every firm instead of
        each firm's own `years_to_maturity`. Useful for sensitivity checks;
        leave as None to use the (more correct) firm-specific maturity.
    """
    rows = []
    for firm in portfolio:
        ead, lgd = firm["ead"], firm["lgd"]
        pd_ = float(transition_matrix_n.loc[firm["rating"], "D"])

        # --- Correction vs. the original notebook -----------------------
        # The original hardcoded M = 2.5 for every firm, discarding the
        # firm-specific `years_to_maturity` that was already sitting right
        # there in the portfolio data. Basel's maturity adjustment only
        # does its job when M reflects the exposure's own remaining life
        # (floored/capped at 1 and 5 years, per the IRB rules).
        if maturity_override is not None:
            m = maturity_override
        else:
            m = float(np.clip(firm.get("years_to_maturity", 2.5), 1.0, 5.0))

        exp_factor = np.exp(-50 * pd_)
        denom = 1 - np.exp(-50)
        corr = 0.12 * ((1 - exp_factor) / denom) + 0.24 * (1 - (1 - exp_factor) / denom)
        b = (0.11852 - 0.05478 * np.log(pd_)) ** 2
        maturity_adjustment = (1 + (m - 2.5) * b) / (1 - 1.5 * b)

        wcdr = norm.cdf(
            (1 - corr) ** -0.5 * norm.ppf(pd_) + (corr / (1 - corr)) ** 0.5 * norm.ppf(BASEL_CONFIDENCE)
        )
        el_rate = pd_ * lgd
        k_ratio = (lgd * wcdr - el_rate) * maturity_adjustment

        economic_capital = k_ratio * ead
        expected_loss = el_rate * ead

        rows.append({
            "Firm Name": firm["name"], "Rating": firm["rating"], "PD": pd_,
            "Maturity (M)": m, "Correlation": corr,
            "Expected Loss": expected_loss, "Capital Requirement": economic_capital,
            "CVaR (Total Risk)": economic_capital + expected_loss, "WCDR": wcdr,
        })

    results = pd.DataFrame(rows)
    return {
        "results": results,
        "expected_loss": float(results["Expected Loss"].sum()),
        "var": float(results["CVaR (Total Risk)"].sum()),
        "economic_capital": float(results["Capital Requirement"].sum()),
    }
