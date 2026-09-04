"""
basel_single_factor.py
=======================
Basel II/III Internal Ratings-Based (IRB) single-factor regulatory
capital model -- the ASRF (Asymptotic Single Risk Factor) framework.

Model idea
----------
Basel's IRB formula gives a closed-form (no simulation needed) estimate
of the loss a bank should be capitalised against at a fixed 99.9%
confidence level, derived from the single-factor Vasicek/Merton model
under the assumption of an infinitely granular portfolio.

For each obligor:

    R = 0.12 * w + 0.24 * (1 - w),   w = (1 - e^(-50 PD)) / (1 - e^(-50))
        (Basel's prescribed corporate asset-correlation formula --
         note LOWER-PD firms get a HIGHER correlation R)

    WCDR = N[ N^-1(PD)/sqrt(1-R) + sqrt(R/(1-R)) * N^-1(0.999) ]

    K   = LGD * WCDR - LGD * PD          (capital requirement, % of EAD)
    EL  = PD * LGD * EAD                 (expected loss, currency)
    Capital Requirement ($) = K * EAD

Convention note: this R plays the same structural role as
`asset_correlation` in kmv_montecarlo.py (both are the "R = variance
explained by the market factor" convention) -- see that module's
docstring, and docs/06_correlation_conventions.md, for how this differs
from the plain-rho convention used in credit_var_ratings.py.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import norm


@dataclass
class FirmCapitalResult:
    name: str
    ead: float
    pd: float
    lgd: float
    correlation: float
    expected_loss: float
    capital_requirement: float
    cvar: float  # capital_requirement + expected_loss


def basel_asset_correlation(pd_value: float) -> float:
    """Basel's prescribed corporate asset-correlation formula, R(PD)."""
    w = (1 - np.exp(-50 * pd_value)) / (1 - np.exp(-50))
    return 0.12 * w + 0.24 * (1 - w)


def basel_capital_single_firm(ead: float, lgd: float, pd_value: float, confidence: float = 0.999) -> dict:
    R = basel_asset_correlation(pd_value)
    el = pd_value * ead * lgd
    wcdr = norm.cdf(
        (1 - R) ** -0.5 * norm.ppf(pd_value) + (R / (1 - R)) ** 0.5 * norm.ppf(confidence)
    )
    capital = ead * lgd * wcdr - el
    return {
        "Capital Requirement": capital,
        "Correlation": R,
        "Expected Loss": el,
        "CVaR": capital + el,
    }


def run_portfolio_capital(portfolio, confidence: float = 0.999) -> pd.DataFrame:
    """
    portfolio: list of dicts with keys name, ead, pd, LGD.

    Returns a per-firm DataFrame. Sum the numeric columns for the
    portfolio aggregate -- Basel's ASRF formula is additive across
    obligors by construction (that additivity is *the* simplifying
    assumption behind IRB capital; it assumes idiosyncratic risk is
    fully diversified away, which is a much stronger assumption than
    the finite-portfolio Monte Carlo models elsewhere in this repo).
    """
    rows = []
    for firm in portfolio:
        metrics = basel_capital_single_firm(firm["ead"], firm["LGD"], firm["pd"], confidence)
        rows.append({
            "Firm": firm["name"],
            "EAD": firm["ead"],
            "PD": firm["pd"],
            "LGD": firm["LGD"],
            "Correlation (R)": metrics["Correlation"],
            "Expected Loss": metrics["Expected Loss"],
            "Capital Requirement (K)": metrics["Capital Requirement"],
            "CVaR": metrics["CVaR"],
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    portfolio = [
        {"name": "Firm_1", "ead": 1_000_000, "pd": 0.04, "LGD": 0.3},
        {"name": "Firm_2", "ead": 5_000_000, "pd": 0.10, "LGD": 0.3},
    ]
    df = run_portfolio_capital(portfolio)
    print(df)
    print(f"\nTotal Portfolio Capital Requirement: {df['Capital Requirement (K)'].sum():,.2f}")
    print(f"Total Portfolio Expected Loss:      {df['Expected Loss'].sum():,.2f}")
    print(f"Total Portfolio CVaR:                {df['CVaR'].sum():,.2f}")
