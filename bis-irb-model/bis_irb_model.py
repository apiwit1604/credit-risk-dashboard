# -*- coding: utf-8 -*-
"""
BIS / Basel Single-Factor IRB Model
====================================

Implements the Basel II/III Internal Ratings-Based (IRB) formula for
regulatory capital on a corporate exposure, using the Basel single-factor
Gaussian copula (Vasicek) framework.

Unlike the CreditMetrics and KMV models in this repository, this is a
CLOSED-FORM regulatory formula, not a Monte Carlo simulation. There is no
`N_SIMULATIONS` and no empirical percentile — the 99.9% confidence level
is a fixed constant baked into Basel's calibration
(`norm.ppf(0.999)` below), not a parameter you can vary to test other
confidence levels. This is a deliberate regulatory design choice (Basel
capital requirements are always calibrated to a 99.9% solvency standard),
not an oversight in this implementation. See the repo root README for how
this affects cross-model alpha comparisons.

References
----------
Basel Committee on Banking Supervision, "International Convergence of
Capital Measurement and Capital Standards: A Revised Framework" (Basel II),
IRB risk-weight formulas for corporate, sovereign, and bank exposures.
"""

import numpy as np
from scipy.stats import norm

# Fixed by Basel regulation — not user-configurable. This is the regulatory
# solvency confidence level baked into the IRB formula itself.
BASEL_CONFIDENCE_LEVEL = 0.999


def get_single_factor_bis(lgd: float, pd: float) -> dict:
    """
    Compute Basel single-factor IRB capital requirement for one exposure.

    Parameters
    ----------
    lgd : float
        Loss Given Default, expressed as a DECIMAL fraction of exposure,
        e.g. 0.40 for 40% loss severity. Do NOT pass a percentage integer
        (40) — this silently produces meaningless output rather than
        raising an error, since Python performs the arithmetic regardless.
    pd : float
        Probability of Default over a 1-year horizon, as a decimal
        fraction, e.g. 0.10 for 10%.

    Returns
    -------
    dict with keys:
        "Capital Requirement" : Basel K factor (Economic Capital), i.e.
            unexpected loss capital held above expected loss.
        "Correlation"         : Basel's asset correlation R(PD), which
            declines as PD rises (higher-PD/riskier firms get LOWER
            asset correlation in Basel's corporate formula).
        "Expected Loss"       : PD * LGD.
        "CVaR"                : Capital Requirement + Expected Loss,
            i.e. total unexpected + expected loss at the 99.9% level.

    Raises
    ------
    ValueError
        If lgd or pd fall outside the valid (0, 1) decimal range — this
        guards against the classic mistake of passing 40 instead of 0.40.
    """
    if not (0.0 <= lgd <= 1.0):
        raise ValueError(
            f"lgd must be a decimal fraction in [0, 1], got {lgd}. "
            f"Did you mean {lgd / 100:.4f}?"
        )
    if not (0.0 < pd < 1.0):
        raise ValueError(
            f"pd must be a decimal fraction in (0, 1), got {pd}. "
            f"Did you mean {pd / 100:.4f}?"
        )

    expected_loss = pd * lgd

    # Basel corporate asset correlation formula: R(PD) interpolates between
    # 12% (high-PD / low-quality names) and 24% (low-PD / high-quality
    # names) using an exponential weighting function of PD.
    correlation = (
        0.12 * (1 - np.exp(-50 * pd)) / (1 - np.exp(-50))
        + 0.24 * (1 - (1 - np.exp(-50 * pd)) / (1 - np.exp(-50)))
    )

    capital_requirement = lgd * norm.cdf(
        (1 - correlation) ** -0.5 * norm.ppf(pd)
        + (correlation / (1 - correlation)) ** 0.5 * norm.ppf(BASEL_CONFIDENCE_LEVEL)
    ) - expected_loss

    return {
        "Capital Requirement": capital_requirement,
        "Correlation": correlation,
        "Expected Loss": expected_loss,
        "CVaR": capital_requirement + expected_loss,
    }


if __name__ == "__main__":
    # Demo run — LGD=0.40 (40%), PD=0.10 (10%)
    result = get_single_factor_bis(lgd=0.40, pd=0.10)

    print(f"Capital Requirement (K) : {result['Capital Requirement']:.6f}")
    print(f"Correlation             : {result['Correlation']:.6f}")
    print(f"Expected Loss           : {result['Expected Loss']:.6f}")
    print(f"CVaR                    : {result['CVaR']:.6f}")
