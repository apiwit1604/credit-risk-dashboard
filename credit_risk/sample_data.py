"""
sample_data.py
==============
Default input data used by the dashboard and by each module's example
run. Centralised here so the whole toolkit is demoed consistently.

Data below is illustrative / hypothetical (as noted by the original
author for the rate & spread curves), NOT live market data.
"""

RATING_LABELS = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]

# 1-year ratings transition matrix (source: ThaiBMA, last update 29 Jun 2026)
TRANSITION_MATRIX = [
    [0.90283757199117, 0.08979708745310, 0.00511517223775, 0.00030281809281, 0.00100348769809, 0.00030174443474, 0.00050174199043, 0.00014037610192],
    [0.00454425357289, 0.91201999875982, 0.07738912310741, 0.00447367743335, 0.00052565958818, 0.00062767430464, 0.00021059740922, 0.00020901582448],
    [0.00058723255688, 0.02473496530057, 0.94614192539873, 0.02556653768183, 0.00154614162461, 0.00015850657521, 0.00002524154666, 0.00123944931551],
    [0.00000942967104, 0.00046893331223, 0.03710987290436, 0.91123947383181, 0.03863004389088, 0.00246958593389, 0.00009348733236, 0.00997917312343],
    [0.00001045968432, 0.00007051362091, 0.00138609014070, 0.06771256814916, 0.85372511486569, 0.05032674033410, 0.00187976336150, 0.02488874984362],
    [0.00001004594996, 0.00019214599641, 0.00057371276818, 0.00216518028682, 0.05363942517782, 0.83996077189669, 0.05734399526098, 0.04611472266314],
    [0.00000514179489, 0.00001846823268, 0.00081580258838, 0.00150188444965, 0.00532733655436, 0.15406144871610, 0.52978418567794, 0.30848573198599],
    [0.00000000000000, 0.00000000000000, 0.00000000000000, 0.00000000000000, 0.00000000000000, 0.00000000000000, 0.00000000000000, 1.00000000000000],
]

# (tenor_years, risk_free_rate)
RATE_CURVE = [
    (0.08, 0.0086), (0.25, 0.0087), (0.50, 0.0089), (1.00, 0.0095),
    (2.00, 0.0118), (3.00, 0.0127), (4.00, 0.0147), (5.00, 0.0160),
]

# (tenor_years, spread_AAA_bps, AA, A, BBB, BB, B, CCC) — hypothetical
CREDIT_SPREAD_BPS = [
    (0.08, 10, 20, 30, 40, 50, 60, 70),
    (0.25, 20, 30, 40, 50, 60, 70, 80),
    (0.50, 40, 60, 80, 100, 120, 140, 160),
    (1.00, 50, 80, 100, 120, 150, 180, 200),
    (2.00, 80, 100, 120, 150, 180, 200, 250),
    (3.00, 100, 120, 140, 170, 200, 250, 300),
    (4.00, 150, 180, 200, 250, 270, 300, 350),
    (5.00, 200, 220, 260, 300, 350, 400, 450),
]


def build_spot_curve_by_rating(rate_curve=RATE_CURVE, credit_spread_bps=CREDIT_SPREAD_BPS):
    """Corporate spot rate = risk-free rate + rating spread, per tenor.
    Returns rows shaped like credit_spread_bps: (tenor, spot_AAA, spot_AA, ...)
    """
    rf_by_tenor = {t: rf for t, rf in rate_curve}
    rows = []
    for row in credit_spread_bps:
        tenor, *spreads_bps = row
        rf = rf_by_tenor[tenor]
        rows.append(tuple([tenor] + [rf + bps / 10_000 for bps in spreads_bps]))
    return rows


# Credit-VaR (ratings migration) sample portfolio.
# NOTE: Firm_2's payments_per_year was corrected from 9 -> 1 to match its
# original "จ่าย Annually" (pays annually) comment -- see chat write-up.
CREDIT_VAR_PORTFOLIO = [
    {
        "name": "Firm_1", "rating": "A", "years_to_maturity": 1,
        "asset_correlation": 0.15,  # plain-rho convention (see module docstring)
        "ead": 1_000_000, "coupon_rate": 0.04, "payments_per_year": 2, "LGD": 0.3,
    },
    {
        "name": "Firm_2", "rating": "BB", "years_to_maturity": 2,
        "asset_correlation": 0.20,
        "ead": 500_000, "coupon_rate": 0.06, "payments_per_year": 1, "LGD": 0.4,
    },
]

# KMV Monte Carlo sample portfolio (Basel-R convention -- see module docstring)
KMV_PORTFOLIO = [
    {"name": "Firm_1", "asset": 100_000, "debt": 120_000, "mean": 0.10,
     "standard_deviation": 0.30, "lgd": 0.30, "asset_correlation": 0.23},
    {"name": "Firm_2", "asset": 150_000, "debt": 120_000, "mean": 0.19,
     "standard_deviation": 0.35, "lgd": 0.21, "asset_correlation": 0.70},
    {"name": "Firm_3", "asset": 180_000, "debt": 120_000, "mean": 0.75,
     "standard_deviation": 0.80, "lgd": 0.15, "asset_correlation": 0.10},
]

# Basel single-factor sample portfolio
BASEL_PORTFOLIO = [
    {"name": "Firm_1", "ead": 1_000_000, "pd": 0.04, "LGD": 0.3},
    {"name": "Firm_2", "ead": 5_000_000, "pd": 0.10, "LGD": 0.3},
]

# Merton single-firm sample inputs
MERTON_SAMPLE = dict(S=47_040_000_000, D=25_982_894_373, sigma_E=0.328098346624424, r=0.0199, T=1)

# Bond credit-spread sample curves
BOND_SPREAD_SAMPLE = dict(
    risk_free_rates=[0.045000, 0.046250, 0.047500, 0.048750],
    risky_rates=[0.051250, 0.053750, 0.056250, 0.068750],
)

# Bond price-calibration sample inputs
BOND_CALIBRATION_SAMPLE = dict(
    flat=dict(market_price=80, face_value=100, coupon=4, recovery=10, risk_free_rates=[0.02, 0.03, 0.04, 0.05]),
    term=dict(market_price=80, face_value=100, coupon=20, recovery=0, risk_free_rates=[0.02, 0.03, 0.04, 0.05]),
)
