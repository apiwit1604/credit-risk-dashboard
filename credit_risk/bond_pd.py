"""
bond_pd.py
==========
Bootstraps risk-neutral default probabilities from a term structure of
risk-free and risky (corporate) spot rates, using the reduced-form
"credit spread" approach.

Model idea
----------
Under risk-neutral pricing, a riskless zero-coupon bond and a defaultable
zero-coupon bond promising the same face value satisfy:

    Price_risky(t) / Price_riskless(t) = Cumulative Survival Probability(0, t)

because the risky price already embeds the market's discount for the
chance of default (assuming zero recovery on the defaulted claim). This
ratio gives the cumulative default probability directly; differencing it
across periods gives the unconditional (period-t) and conditional
(forward, given survival to t-1) default probabilities.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BondSpreadPDResult:
    period: np.ndarray
    credit_spread: np.ndarray
    price_riskless: np.ndarray
    price_risky: np.ndarray
    cum_survival_prob: np.ndarray
    cum_default_prob: np.ndarray
    unconditional_pd: np.ndarray
    conditional_pd: np.ndarray

    def prices_table(self) -> pd.DataFrame:
        return pd.DataFrame({
            "Period t": self.period,
            "Credit Spread": np.round(self.credit_spread, 6),
            "Price of Riskless Bond": np.round(self.price_riskless, 2),
            "Price of Risky Bond": np.round(self.price_risky, 2),
        })

    def pd_table(self, as_percent: bool = True) -> pd.DataFrame:
        df = pd.DataFrame({
            "Period t": self.period,
            "Cumulative Solvency Probability": self.cum_survival_prob,
            "Cumulative Default Probability": self.cum_default_prob,
            "Unconditional PD (period t)": self.unconditional_pd,
            "Conditional PD (t | survived to t-1)": self.conditional_pd,
        })
        if as_percent:
            for col in df.columns[1:]:
                df[col] = (df[col] * 100).round(2).astype(str) + "%"
        return df


def price_zero_coupon(spot_rates, face_value: float = 100.0) -> np.ndarray:
    """Price a zero-coupon claim paying `face_value` at each period t,
    discounted at the spot rate quoted for that maturity: P_t = FV / (1+r_t)^t
    """
    rate = np.asarray(spot_rates, dtype=float)
    t = np.arange(1, len(rate) + 1)
    return face_value / (1.0 + rate) ** t


def bootstrap_pd_from_spread(risk_free_rates, risky_rates, face_value: float = 100.0) -> BondSpreadPDResult:
    """Bootstrap the full PD term structure implied by the spread between
    a risk-free and a risky spot-rate curve of the same maturities.
    """
    rf = np.asarray(risk_free_rates, dtype=float)
    r = np.asarray(risky_rates, dtype=float)
    if rf.shape != r.shape:
        raise ValueError(f"risk_free_rates has {rf.size} points but risky_rates has {r.size}.")

    n = rf.size
    period = np.arange(1, n + 1)

    price_riskless = price_zero_coupon(rf, face_value)
    price_risky = price_zero_coupon(r, face_value)

    cum_survival = price_risky / price_riskless      # bond-price parity
    cum_default = 1.0 - cum_survival

    unconditional_pd = np.zeros(n)
    conditional_pd = np.zeros(n)
    for t in range(n):
        if t == 0:
            unconditional_pd[t] = cum_default[t]
            conditional_pd[t] = unconditional_pd[t]
        else:
            unconditional_pd[t] = cum_default[t] - cum_default[t - 1]
            conditional_pd[t] = unconditional_pd[t] / cum_survival[t - 1]

    return BondSpreadPDResult(
        period=period,
        credit_spread=r - rf,
        price_riskless=price_riskless,
        price_risky=price_risky,
        cum_survival_prob=cum_survival,
        cum_default_prob=cum_default,
        unconditional_pd=unconditional_pd,
        conditional_pd=conditional_pd,
    )


if __name__ == "__main__":
    rf = [0.045000, 0.046250, 0.047500, 0.048750]
    r = [0.051250, 0.053750, 0.056250, 0.068750]
    result = bootstrap_pd_from_spread(rf, r)
    print(result.prices_table())
    print(result.pd_table())
