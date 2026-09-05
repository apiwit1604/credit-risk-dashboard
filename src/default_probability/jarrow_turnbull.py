# -*- coding: utf-8 -*-
"""
Jarrow & Turnbull (1995) reduced-form default model: default is a
risk-neutral hazard process calibrated so the model's defaultable bond
price matches an observed market price, discounting expected cash flows
(weighted by survival/default probabilities) on the risk-free curve.

Two calibration variants:
  * `run_jarrow_turnbull_one_pd`  — a single, constant hazard rate.
  * `run_jarrow_turnbull_many_pd` — one hazard rate per coupon period
    (a simple term structure of default probabilities).
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.optimize import minimize


def _build_paytimes(bond_years: float, freq: int) -> np.ndarray:
    if freq == 0:
        return np.array([bond_years])
    paytimes = np.arange(bond_years, 0, -1 / freq)
    return np.sort(paytimes)  # ascending: nearest payment date first


def run_jarrow_turnbull_one_pd(
    market_price: float,
    face_value: float,
    coupon_rate: float,
    freq: int,
    bond_years: float,
    recovery_rate: float,
    rf: Sequence[Tuple[float, float]],
) -> Tuple[float, float, np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    paytimes = _build_paytimes(bond_years, freq)
    n = len(paytimes)
    coupon = 0.0 if (coupon_rate == 0 or freq == 0) else face_value * coupon_rate / freq

    tenors, rf_rates = zip(*rf)
    interpolator = CubicSpline(tenors, rf_rates)

    def calc_price(pd_flat: float):
        pd_flat = float(np.clip(pd_flat, 0, 1))
        # --- Cleaner vs. the original notebook --------------------------
        # The original built paytimes in *descending* order and then
        # called np.sort() on the resulting probability arrays as an
        # implicit "reverse" trick to line them back up with time. That
        # only works by luck for a single constant PD, where the sequence
        # happens to already be monotonic; it gives no guarantee (and no
        # error) if the assumption ever stops holding. Here, `paytimes` is
        # sorted ascending up front and survival/default probabilities are
        # built directly in that same chronological order — the same,
        # already-correct pattern used in `run_jarrow_turnbull_many_pd`.
        survival = np.cumprod(np.full(n, 1 - pd_flat))
        survival = np.insert(survival[:-1], 0, 1.0)  # survival *before* each period's own default draw
        prob_default = survival * pd_flat
        prob_survival = survival * (1 - pd_flat)

        expected_cf = np.where(
            np.isclose(paytimes, bond_years),
            prob_default * recovery_rate + prob_survival * (face_value + coupon),
            prob_default * recovery_rate + prob_survival * coupon,
        )
        discount = (1 + interpolator(paytimes)) ** -paytimes
        pv_expected_cf = expected_cf * discount

        table = pd.DataFrame({
            "Zero_Rate": interpolator(paytimes), "Discount_Factor": discount,
            "Prob_Survival": prob_survival, "Prob_Default": prob_default,
            "Expected_CF": expected_cf, "PV_Expected_CF": pv_expected_cf,
        }, index=paytimes)
        table.index.name = "Paytime_Years"
        return float(pv_expected_cf.sum()), expected_cf, pv_expected_cf, discount, table

    def objective(params):
        price, *_ = calc_price(params[0])
        return (price - market_price) ** 2

    result = minimize(objective, x0=[0.01], bounds=[(0, 1)])
    pd_opt = float(result.x[0])
    price_calc, expected_cf, pv_cf, discount, table = calc_price(pd_opt)
    return pd_opt, price_calc, expected_cf, pv_cf, discount, table


def run_jarrow_turnbull_many_pd(
    market_price: float,
    face_value: float,
    coupon_rate: float,
    freq: int,
    bond_years: float,
    recovery_rate: float,
    rf: Sequence[Tuple[float, float]],
) -> Tuple[np.ndarray, float, np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    paytimes = _build_paytimes(bond_years, freq)
    n = len(paytimes)
    coupon = 0.0 if (coupon_rate == 0 or freq == 0) else face_value * coupon_rate / freq

    tenors, rf_rates = zip(*rf)
    interpolator = CubicSpline(tenors, rf_rates)

    def calc_price(pds: np.ndarray):
        pds = np.clip(pds, 0, 1)
        surv_running = 1.0
        expected_cf = np.zeros(n)
        prob_default = np.zeros(n)
        prob_survival = np.zeros(n)

        for t in range(n):
            p = pds[t]
            prob_default[t] = surv_running * p
            prob_survival[t] = surv_running * (1 - p)
            is_last = (t == n - 1)
            expected_cf[t] = prob_default[t] * recovery_rate + prob_survival[t] * (
                (face_value + coupon) if is_last else coupon
            )
            surv_running *= (1 - p)

        discount = (1 + interpolator(paytimes)) ** -paytimes
        pv_expected_cf = expected_cf * discount

        table = pd.DataFrame({
            "Zero_Rate": interpolator(paytimes), "PD": pds, "Discount_Factor": discount,
            "Prob_Survival": prob_survival, "Prob_Default": prob_default,
            "Expected_CF": expected_cf, "PV_Expected_CF": pv_expected_cf,
        }, index=paytimes)
        table.index.name = "Paytime_Years"
        return float(pv_expected_cf.sum()), expected_cf, pv_expected_cf, discount, table

    def objective(pds):
        price, *_ = calc_price(pds)
        return (price - market_price) ** 2

    result = minimize(objective, x0=np.full(n, 0.05), bounds=[(0, 1)] * n)
    pd_opt: np.ndarray = np.clip(result.x, 0, 1)
    price_calc, expected_cf, pv_cf, discount, table = calc_price(pd_opt)
    return pd_opt, price_calc, expected_cf, pv_cf, discount, table
