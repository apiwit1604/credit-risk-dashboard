"""
merton.py
=========
Merton (1974) structural credit model: equity is viewed as a European
call option on the firm's asset value, struck at the face value of debt.
Calibrates the unobservable firm asset value (V) and asset volatility
(sigma_V) from two *observable* market quantities -- equity value (S)
and equity volatility (sigma_E) -- then backs out the risk-neutral
probability of default.

Model idea
----------
Under Black-Scholes/Merton assumptions, equity value satisfies

    S = V * N(d1) - D * exp(-rT) * N(d2)

    d1 = [ln(V/D) + (r + 0.5 sigma_V^2) T] / (sigma_V sqrt(T))
    d2 = d1 - sigma_V sqrt(T)

and, by Ito's lemma applied to the option-pricing relationship, equity
volatility links to asset volatility via

    sigma_E * S = N(d1) * sigma_V * V

That's two equations in two unknowns (V, sigma_V); we solve them jointly
by minimizing the sum of squared pricing/volatility errors (SSE), the
standard "KMV-style" calibration approach.

The (risk-neutral) probability of default over horizon T is then

    PD = N(-d2) = P(V_T < D)   under the risk-neutral measure.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm


@dataclass
class MertonResult:
    firm_value: float
    asset_volatility: float
    implied_call_value: float  # should converge to S
    sse: float
    d1: float
    d2: float
    default_probability_rn: float  # risk-neutral-world PD

    def summary_table(self) -> pd.DataFrame:
        return pd.DataFrame({
            "Parameter": ["Optimal Firm Value (V)", "Optimal Asset Vol (sigma_V)",
                          "Call on Firm Value (~ S)", "SSE"],
            "Value": [self.firm_value, self.asset_volatility, self.implied_call_value, self.sse],
        })

    def pd_table(self) -> pd.DataFrame:
        return pd.DataFrame({
            "Probability of Default": ["Risk-Neutral World"],
            "Value": [self.default_probability_rn],
        })


def _sse(params, S, D, sigma_E, r, T):
    V, sigma_V = params
    if V <= 0 or sigma_V <= 0:
        return 1e10  # keep the optimizer out of an undefined region

    d1 = (np.log(V / D) + (r + 0.5 * sigma_V ** 2) * T) / (sigma_V * np.sqrt(T))
    d2 = d1 - sigma_V * np.sqrt(T)
    call = V * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)
    implied_sigma_E = norm.cdf(d1) * sigma_V * V / S

    return (S - call) ** 2 + 1e6 * (sigma_E - implied_sigma_E) ** 2


def calibrate_merton(S, D, sigma_E, r, T: float = 1.0, v0_guess=None, sigmav0_guess=None) -> MertonResult:
    """
    S       : market value of equity
    D       : face value of debt (the Merton "default point")
    sigma_E : (annualized) equity volatility
    r       : risk-free rate
    T       : horizon in years

    Note on initial guess: a firm's asset value is at least S + D (equity
    plus debt), so seeding the optimizer at V0 = S alone can bias
    Nelder-Mead toward a poor local optimum for highly levered firms.
    We default to V0 = S + D instead.
    """
    v0_guess = v0_guess if v0_guess is not None else S + D
    sigmav0_guess = sigmav0_guess if sigmav0_guess is not None else sigma_E

    result = minimize(_sse, x0=[v0_guess, sigmav0_guess], args=(S, D, sigma_E, r, T), method="Nelder-Mead")
    V_opt, sigmaV_opt = result.x

    d1 = (np.log(V_opt / D) + (r + 0.5 * sigmaV_opt ** 2) * T) / (sigmaV_opt * np.sqrt(T))
    d2 = d1 - sigmaV_opt * np.sqrt(T)
    call = V_opt * norm.cdf(d1) - D * np.exp(-r * T) * norm.cdf(d2)
    pd_rn = 1 - norm.cdf(d2)

    return MertonResult(
        firm_value=V_opt, asset_volatility=sigmaV_opt, implied_call_value=call,
        sse=float(result.fun), d1=d1, d2=d2, default_probability_rn=pd_rn,
    )


if __name__ == "__main__":
    res = calibrate_merton(S=47_040_000_000, D=25_982_894_373, sigma_E=0.328098346624424, r=0.0199, T=1)
    print(res.summary_table())
    print(res.pd_table())
