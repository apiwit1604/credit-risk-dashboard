# -*- coding: utf-8 -*-
"""
Default model inputs for the credit risk toolkit.

These are the "hard to calibrate" market/model parameters exposed on the
dashboard's Settings page (rating scale, transition matrix, risk-free curve
and credit-spread curve), plus a small demo portfolio used to seed the app.

Nothing here is a magic number pulled out of thin air — the transition
matrix and curves are the ones from the original notebook (ThaiBMA, last
update 29 Jun 2026); the demo portfolio is a synthetic 3-firm book used
for illustration only.
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Rating scale & transition matrix
# ---------------------------------------------------------------------------
DEFAULT_RATING_LABELS: List[str] = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]

# 1-year rating transition matrix. Source: ThaiBMA (last update 29 Jun 2026).
# Row i = starting rating, column j = ending rating, values = probability.
# "D" (default) is an absorbing state: its row is [0, 0, ..., 0, 1].
DEFAULT_TRANSITION_MATRIX: np.ndarray = np.array([
    [0.90283757199117, 0.08979708745310, 0.00511517223775, 0.00030281809281,
     0.00100348769809, 0.00030174443474, 0.00050174199043, 0.00014037610192],
    [0.00454425357289, 0.91201999875982, 0.07738912310741, 0.00447367743335,
     0.00052565958818, 0.00062767430464, 0.00021059740922, 0.00020901582448],
    [0.00058723255688, 0.02473496530057, 0.94614192539873, 0.02556653768183,
     0.00154614162461, 0.00015850657521, 0.00002524154666, 0.00123944931551],
    [0.00000942967104, 0.00046893331223, 0.03710987290436, 0.91123947383181,
     0.03863004389088, 0.00246958593389, 0.00009348733236, 0.00997917312343],
    [0.00001045968432, 0.00007051362091, 0.00138609014070, 0.06771256814916,
     0.85372511486569, 0.05032674033410, 0.00187976336150, 0.02488874984362],
    [0.00001004594996, 0.00019214599641, 0.00057371276818, 0.00216518028682,
     0.05363942517782, 0.83996077189669, 0.05734399526098, 0.04611472266314],
    [0.00000514179489, 0.00001846823268, 0.00081580258838, 0.00150188444965,
     0.00532733655436, 0.15406144871610, 0.52978418567794, 0.30848573198599],
    [0.00000000000000, 0.00000000000000, 0.00000000000000, 0.00000000000000,
     0.00000000000000, 0.00000000000000, 0.00000000000000, 1.00000000000000],
])

# ---------------------------------------------------------------------------
# Risk-free curve (annually-compounded zero rates) and the credit-spread
# curve (basis points over risk-free). Columns of the spread curve line up
# with DEFAULT_RATING_LABELS[:-1] (every rating except "D").
# ---------------------------------------------------------------------------
DEFAULT_RF_DATA: List[Tuple[float, float]] = [
    (0.08, 0.00915),
    (0.25, 0.00956),
    (0.50, 0.00974),
    (1.00, 0.00993),
    (2.00, 0.01231),
    (3.00, 0.01329),
    (4.00, 0.01523),
    (5.00, 0.01671),
]

DEFAULT_CREDIT_SPREAD_DATA: List[Tuple[float, ...]] = [
    (0.08, 15, 20, 30, 55, 100, 180, 300),
    (0.25, 15, 22, 32, 60, 110, 200, 330),
    (0.50, 18, 25, 35, 65, 120, 220, 360),
    (1.00, 20, 28, 40, 75, 135, 250, 400),
    (2.00, 25, 35, 50, 90, 160, 300, 480),
    (3.00, 30, 42, 60, 105, 190, 350, 560),
    (4.00, 35, 50, 70, 120, 220, 400, 650),
    (5.00, 40, 58, 80, 135, 250, 450, 750),
]

# ---------------------------------------------------------------------------
# Sample demo portfolio (3 firms) — purely illustrative starting point,
# fully editable on the dashboard.
# ---------------------------------------------------------------------------
DEFAULT_PORTFOLIO: List[dict] = [
    {
        "name": "Firm_1", "rating": "A", "years_to_maturity": 1,
        "asset_correlation": 0.55, "asset_value": 100, "ead": 80,
        "asset_mean": 0.08, "asset_std": 0.50,
        "coupon_rate": 0.04, "payments_per_year": 2, "lgd": 0.30,
    },
    {
        "name": "Firm_2", "rating": "BB", "years_to_maturity": 2,
        "asset_correlation": 0.55, "asset_value": 150, "ead": 120,
        "asset_mean": 0.12, "asset_std": 0.70,
        "coupon_rate": 0.06, "payments_per_year": 4, "lgd": 0.60,
    },
    {
        "name": "Firm_3", "rating": "BBB", "years_to_maturity": 3,
        "asset_correlation": 0.50, "asset_value": 200, "ead": 160,
        "asset_mean": 0.10, "asset_std": 0.60,
        "coupon_rate": 0.05, "payments_per_year": 2, "lgd": 0.45,
    },
]

DEFAULT_LOSS_HORIZON: float = 1.0

# Dashboard defaults are lower than the original 1,000,000 purely so the UI
# stays responsive on every widget interaction (Streamlit reruns the script
# top-to-bottom on each one). Push this back up to 1,000,000 on the Settings
# page for final, report-quality numbers — results are cached, so repeated
# runs with the same inputs are instant.
DEFAULT_N_SIM: int = 200_000
DEFAULT_CONFIDENCE_KMV: float = 0.99
DEFAULT_CONFIDENCE_CREDITMETRICS: float = 0.999

# Fixed by the Basel IRB framework itself — not a user choice, unlike the
# two Monte Carlo models above.
BASEL_CONFIDENCE: float = 0.999
