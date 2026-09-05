# -*- coding: utf-8 -*-
"""
Forward-value revaluation used by the CreditMetrics engine: what is one
exposure worth today (as of the risk horizon) *if* it ends up in a given
future rating, found by discounting its remaining cash flows on that
rating's forward curve (`curves.get_forward_rate`).
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np
import pandas as pd

from .curves import get_forward_rate


def value_forward(
    ead: float,
    rating_end: str,
    payments_per_year: int,
    years_to_maturity: float,
    loss_horizon: float,
    coupon_rate: float,
    lgd: float,
    spot_rating: pd.DataFrame,
) -> float:
    """Present value (as of `loss_horizon`) of one exposure, assuming it
    ends up in rating `rating_end` (or defaults, if `rating_end == "D"`).
    """
    if rating_end == "D":
        return ead * (1 - lgd)

    if years_to_maturity <= loss_horizon:
        coupon = ead * (coupon_rate / payments_per_year) if payments_per_year else 0.0
        return ead + coupon

    if payments_per_year == 0:
        r = get_forward_rate(rating_end, years_to_maturity, spot_rating, loss_horizon)
        return ead / (1 + r) ** (years_to_maturity - loss_horizon)

    base_times = np.arange(loss_horizon, years_to_maturity, 1 / payments_per_year)
    paytimes = np.append(base_times, years_to_maturity)
    coupon = ead * (coupon_rate / payments_per_year)
    cash_flow = np.where(np.isclose(paytimes, years_to_maturity), ead + coupon, coupon)

    # --- Bug fix vs. the original notebook -----------------------------
    # The original computed a forward rate inside a `for` loop meant to
    # build one rate per payment date, but reassigned the SAME scalar
    # variable each iteration instead of storing it — so every cash flow
    # ended up discounted with only the *last* period's forward rate.
    # Each cash flow must use the forward rate matched to its own date.
    forward_rates = np.array([
        get_forward_rate(rating_end, t, spot_rating, loss_horizon) for t in paytimes
    ])
    pv_cash_flow = cash_flow / (1 + forward_rates) ** (paytimes - loss_horizon)
    return float(np.sum(pv_cash_flow))


def calculate_credit_loss(
    portfolio: Sequence[dict],
    rating_labels: Sequence[str],
    loss_horizon: float,
    spot_rating: pd.DataFrame,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """For every firm in `portfolio`, value the exposure under every
    possible ending rating, and under its current rating (the reference
    value used to measure loss: value_begin - value_end).

    Returns (value_matrix_n, value_matrix_begin, loss), each of shape
    (n_firms, n_ratings), column order following `rating_labels`.
    """
    rating_labels = list(rating_labels)
    n_firms, n_ratings = len(portfolio), len(rating_labels)
    value_matrix_n = np.zeros((n_firms, n_ratings))
    value_matrix_begin = np.zeros((n_firms, n_ratings))

    for i, firm in enumerate(portfolio):
        firm_value_begin = value_forward(
            ead=firm["ead"], rating_end=firm["rating"],
            payments_per_year=firm["payments_per_year"],
            years_to_maturity=firm["years_to_maturity"],
            loss_horizon=loss_horizon, coupon_rate=firm["coupon_rate"],
            lgd=firm["lgd"], spot_rating=spot_rating,
        )
        value_matrix_begin[i, :] = firm_value_begin  # same reference value across the row

        for k, rating_end in enumerate(rating_labels):
            value_matrix_n[i, k] = value_forward(
                ead=firm["ead"], rating_end=rating_end,
                payments_per_year=firm["payments_per_year"],
                years_to_maturity=firm["years_to_maturity"],
                loss_horizon=loss_horizon, coupon_rate=firm["coupon_rate"],
                lgd=firm["lgd"], spot_rating=spot_rating,
            )

    loss = value_matrix_begin - value_matrix_n
    return value_matrix_n, value_matrix_begin, loss
