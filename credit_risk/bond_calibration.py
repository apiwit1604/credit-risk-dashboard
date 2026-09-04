"""
bond_calibration.py
====================
Calibrates the default probability implied by a bond's *observed market
price*, given its promised cash flows (face value, coupon), a recovery
assumption, and the risk-free spot curve.

Model idea
----------
Price a defaultable coupon bond as the risk-neutral expected value of its
cash flows: in each period the bond either survives (pays the coupon, or
principal + coupon at maturity) or defaults (pays a fixed Recovery
Value). Given a candidate PD (or PD term structure), the model price is
computable in closed form; we then solve for the PD(s) that make the
model price match the observed market price (minimize squared pricing
error).

Two variants:
  * `calibrate_flat_pd`          -- a single PD applied to every period.
  * `calibrate_term_structure_pd` -- one PD per period.

IMPORTANT identification caveat: `calibrate_term_structure_pd` fits n
free parameters (one PD per period) against a SINGLE market-price
constraint. The problem is under-identified -- many different PD term
structures can reproduce the same bond price to the optimizer's
tolerance. Treat its period-by-period PD path as illustrative, not
uniquely determined, unless you add more constraints (e.g. several
bonds of different maturities on the same issuer).
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize


@dataclass
class BondCalibrationResult:
    period: np.ndarray
    risk_free_rate: np.ndarray
    expected_cash_flow: np.ndarray
    present_value: np.ndarray
    pd: np.ndarray  # length 1 (flat) or length n (term structure)
    model_price: float
    sse: float

    def cashflow_table(self) -> pd.DataFrame:
        return pd.DataFrame({
            "Period": self.period,
            "Risk-Free Rate": self.risk_free_rate,
            "Expected Cash Flow": np.round(self.expected_cash_flow, 6),
            "PV(Expected Cash Flow)": np.round(self.present_value, 6),
        })

    def pd_table(self) -> pd.DataFrame:
        pd_arr = np.broadcast_to(self.pd, self.period.shape)
        return pd.DataFrame({"Period": self.period, "PD_t": pd_arr})


def _price_with_flat_pd(pd_value, face_value, coupon, recovery, risk_free_rates):
    pd_value = float(np.clip(pd_value, 0.0, 1.0))
    n = len(risk_free_rates)

    survival = np.cumprod(np.full(n, 1 - pd_value))
    survival_prev = np.insert(survival[:-1], 0, 1.0)  # survival probability up to t-1

    prob_default_this_period = survival_prev * pd_value
    prob_survive_this_period = survival_prev * (1 - pd_value)

    cash_flow = prob_default_this_period * recovery + prob_survive_this_period * coupon
    cash_flow[-1] = prob_default_this_period[-1] * recovery + prob_survive_this_period[-1] * (face_value + coupon)

    discount = np.array([(1 + risk_free_rates[t]) ** (t + 1) for t in range(n)])
    pv = cash_flow / discount
    return pv.sum(), cash_flow, pv, discount


def calibrate_flat_pd(market_price, face_value, coupon, recovery, risk_free_rates,
                       initial_guess: float = 0.01) -> BondCalibrationResult:
    risk_free_rates = np.asarray(risk_free_rates, dtype=float)
    n = len(risk_free_rates)

    def objective(x):
        price, *_ = _price_with_flat_pd(x[0], face_value, coupon, recovery, risk_free_rates)
        return (price - market_price) ** 2

    result = minimize(objective, x0=[initial_guess], bounds=[(0, 1)])
    pd_opt = float(np.clip(result.x[0], 0, 1))
    price, cash_flow, pv, _ = _price_with_flat_pd(pd_opt, face_value, coupon, recovery, risk_free_rates)

    return BondCalibrationResult(
        period=np.arange(1, n + 1), risk_free_rate=risk_free_rates,
        expected_cash_flow=cash_flow, present_value=pv,
        pd=np.array([pd_opt]), model_price=price, sse=float(result.fun),
    )


def _price_with_term_structure_pd(pds, face_value, coupon, recovery, risk_free_rates):
    pds = np.clip(pds, 0.0, 1.0)
    n = len(risk_free_rates)
    survival = 1.0
    cash_flow = np.zeros(n)

    for t in range(n):
        p = pds[t]
        prob_default_this_period = survival * p
        prob_survive_this_period = survival * (1 - p)
        if t < n - 1:
            cash_flow[t] = prob_default_this_period * recovery + prob_survive_this_period * coupon
        else:
            cash_flow[t] = prob_default_this_period * recovery + prob_survive_this_period * (face_value + coupon)
        survival *= (1 - p)

    discount = np.array([(1 + risk_free_rates[t]) ** (t + 1) for t in range(n)])
    pv = cash_flow / discount
    return pv.sum(), cash_flow, pv, discount


def calibrate_term_structure_pd(market_price, face_value, coupon, recovery, risk_free_rates,
                                 initial_guess: float = 0.05) -> BondCalibrationResult:
    risk_free_rates = np.asarray(risk_free_rates, dtype=float)
    n = len(risk_free_rates)

    def objective(pds):
        price, *_ = _price_with_term_structure_pd(pds, face_value, coupon, recovery, risk_free_rates)
        return (price - market_price) ** 2

    x0 = np.full(n, initial_guess)
    result = minimize(objective, x0=x0, bounds=[(0, 1)] * n)
    pds_opt = np.clip(result.x, 0, 1)
    price, cash_flow, pv, _ = _price_with_term_structure_pd(pds_opt, face_value, coupon, recovery, risk_free_rates)

    return BondCalibrationResult(
        period=np.arange(1, n + 1), risk_free_rate=risk_free_rates,
        expected_cash_flow=cash_flow, present_value=pv,
        pd=pds_opt, model_price=price, sse=float(result.fun),
    )


if __name__ == "__main__":
    yts = [0.02, 0.03, 0.04, 0.05]

    r1 = calibrate_flat_pd(market_price=80, face_value=100, coupon=4, recovery=10, risk_free_rates=yts)
    print(f"Flat PD: {r1.pd[0] * 100:.4f}%  (SSE={r1.sse:.2e})")

    r2 = calibrate_term_structure_pd(market_price=80, face_value=100, coupon=20, recovery=0, risk_free_rates=yts)
    print(r2.pd_table())
