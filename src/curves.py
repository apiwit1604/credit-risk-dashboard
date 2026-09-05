# -*- coding: utf-8 -*-
"""
Term-structure building blocks shared by every model:

  * the multi-year rating transition matrix (via fractional matrix power),
  * the risk-free curve and rating-specific "risky" spot curves, and
  * a cubic-spline forward-rate lookup used by the CreditMetrics revaluation
    step in `valuation.py`.
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.linalg import fractional_matrix_power


def build_transition_matrix_n(
    transition_matrix: np.ndarray,
    rating_labels: Sequence[str],
    loss_horizon: float,
) -> pd.DataFrame:
    """Raise the 1-year transition matrix to the power of `loss_horizon`.

    A fractional matrix power (rather than a plain matrix product) lets a
    `loss_horizon` shorter or longer than one year still produce a valid
    transition matrix.
    """
    matrix_n = fractional_matrix_power(np.asarray(transition_matrix, dtype=float), loss_horizon)

    # fractional_matrix_power can return tiny complex-noise / slightly
    # negative entries for non-integer powers. Clean up before this reaches
    # probability math (thresholds, cumulative sums, etc.) downstream.
    matrix_n = np.real(matrix_n)
    matrix_n = np.clip(matrix_n, 0, 1)
    matrix_n = matrix_n / matrix_n.sum(axis=1, keepdims=True)

    return pd.DataFrame(matrix_n, index=list(rating_labels), columns=list(rating_labels))


def build_spot_curves(
    rf_data: Sequence[Tuple[float, float]],
    credit_spread_data: Sequence[Tuple[float, ...]],
    rating_labels: Sequence[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build the risk-free curve, the credit-spread curve (bps) and the
    resulting per-rating "risky" spot curve (risk-free + spread / 10,000).

    Returns
    -------
    (risk_free_rate, credit_spread, spot_rating) — each indexed by tenor in
    years. `credit_spread` and `spot_rating` have one column per non-default
    rating (`rating_labels` minus "D").
    """
    non_default_ratings: List[str] = [r for r in rating_labels if r != "D"]

    tenors, rf_rates = zip(*rf_data)
    risk_free_rate = pd.DataFrame({"rF": rf_rates}, index=pd.Index(tenors, name="tenor_years"))

    spread_tenors, *spread_columns = zip(*credit_spread_data)
    if list(spread_tenors) != list(tenors):
        raise ValueError("rf_data and credit_spread_data must share the same tenor grid.")
    if len(spread_columns) != len(non_default_ratings):
        raise ValueError(
            f"credit_spread_data has {len(spread_columns)} rating columns, "
            f"expected {len(non_default_ratings)} (rating_labels minus 'D')."
        )

    credit_spread = pd.DataFrame(
        dict(zip(non_default_ratings, spread_columns)),
        index=pd.Index(tenors, name="tenor_years"),
    )

    spot_rating = credit_spread.divide(10_000).add(risk_free_rate["rF"], axis=0)
    return risk_free_rate, credit_spread, spot_rating


def get_forward_rate(
    rating: str,
    n_years: float,
    spot_rating: pd.DataFrame,
    loss_horizon: float,
) -> float:
    """Forward rate between `n_years` and `n_years + loss_horizon`, implied
    by the cubic-spline-interpolated spot curve for `rating`.
    """
    if rating not in spot_rating.columns:
        raise KeyError(f"Rating '{rating}' not found in spot_rating columns: {list(spot_rating.columns)}")

    tenors = spot_rating.index.values
    spots = spot_rating[rating].values
    curve = CubicSpline(tenors, spots, bc_type="natural")

    rate_start = curve(n_years)
    rate_end = curve(n_years + loss_horizon)

    forward = ((1 + rate_end) ** (n_years + loss_horizon)) / ((1 + rate_start) ** n_years) - 1
    return float(forward)
