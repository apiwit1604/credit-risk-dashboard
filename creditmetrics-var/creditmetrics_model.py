# -*- coding: utf-8 -*-
"""
CreditMetrics-Style Portfolio Credit VaR Model
================================================

Simulates rating migrations (including default) for a portfolio of bonds
using a single-factor Gaussian copula (Vasicek framework), then revalues
each firm's cash flows under every possible year-1 rating outcome to
build a full portfolio loss distribution and compute Credit VaR /
Economic Capital.

This is a MONTE CARLO model — `alpha` is an empirical loss percentile
and can be freely varied and compared against the KMV model in this repo
at the same alpha. See the repo root README for how this differs from
the BIS/Basel closed-form model.

TODO / DATA QUALITY FLAGS (left for the model owner to resolve, not
silently changed by this refactor):
  - Firm_2 is commented "pay Annually" but coded payments_per_year=9.
  - Firm_4 and Firm_5 are commented "Zero-coupon bond" but coded with
    payments_per_year=4 and 6 respectively (a zero-coupon bond should
    have payments_per_year=0, matching Firm_3).
  Verify these against your intended contract terms before treating
  results as final — they currently drive real cash-flow timing in
  value_forward_1y().
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.interpolate import CubicSpline

# ---------------------------------------------------------------------------
# STEP 1: Portfolio configuration
# ---------------------------------------------------------------------------
# Each entry = one firm in the portfolio: current rating, years remaining
# on the contract, and asset correlation with the market.
PORTFOLIO = [
    {
        "name": "Firm_1",
        "rating": "A",
        "years_to_maturity": 1,
        "asset_correlation": 0.15,
        "ead": 1_000_000,
        "coupon_rate": 0.04,
        "payments_per_year": 2,  # Semi-annual
        "LGD": 0.3,
    },
    {
        "name": "Firm_2",
        "rating": "BB",
        "years_to_maturity": 2,
        "asset_correlation": 0.20,
        "ead": 500_000,
        "coupon_rate": 0.06,
        # TODO: comment says "Annually" but value is 9 — verify intent.
        "payments_per_year": 9,
        "LGD": 0.4,
    },
    {
        "name": "Firm_3",
        "rating": "CCC",
        "years_to_maturity": 3,
        "asset_correlation": 0.24,
        "ead": 2_000_000,
        "coupon_rate": 0.00,
        "payments_per_year": 0,  # Zero-coupon bond
        "LGD": 0.4,
    },
    {
        "name": "Firm_4",
        "rating": "AA",
        "years_to_maturity": 4,
        "asset_correlation": 0.60,
        "ead": 1_350_000,
        "coupon_rate": 0.20,
        # TODO: comment says "Zero-coupon bond" but value is 4 — verify intent.
        "payments_per_year": 4,
        "LGD": 0.3,
    },
    {
        "name": "Firm_5",
        "rating": "BBB",
        "years_to_maturity": 4,
        "asset_correlation": 0.60,
        "ead": 3_300_000,
        "coupon_rate": 0.20,
        # TODO: comment says "Zero-coupon bond" but value is 6 — verify intent.
        "payments_per_year": 6,
        "LGD": 0.2,
    },
]

N_SIMULATIONS = 1_000_000

RATING_LABELS = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]

# 1-year rating migration matrix. Source: ThaiBMA (last update 29 June 2026).
TRANSITION_MATRIX = np.array([
    [0.90283757199117, 0.08979708745310, 0.00511517223775, 0.00030281809281, 0.00100348769809, 0.00030174443474, 0.00050174199043, 0.00014037610192],
    [0.00454425357289, 0.91201999875982, 0.07738912310741, 0.00447367743335, 0.00052565958818, 0.00062767430464, 0.00021059740922, 0.00020901582448],
    [0.00058723255688, 0.02473496530057, 0.94614192539873, 0.02556653768183, 0.00154614162461, 0.00015850657521, 0.00002524154666, 0.00123944931551],
    [0.00000942967104, 0.00046893331223, 0.03710987290436, 0.91123947383181, 0.03863004389088, 0.00246958593389, 0.00009348733236, 0.00997917312343],
    [0.00001045968432, 0.00007051362091, 0.00138609014070, 0.06771256814916, 0.85372511486569, 0.05032674033410, 0.00187976336150, 0.02488874984362],
    [0.00001004594996, 0.00019214599641, 0.00057371276818, 0.00216518028682, 0.05363942517782, 0.83996077189669, 0.05734399526098, 0.04611472266314],
    [0.00000514179489, 0.00001846823268, 0.00081580258838, 0.00150188444965, 0.00532733655436, 0.15406144871610, 0.52978418567794, 0.30848573198599],
    [0.00000000000000, 0.00000000000000, 0.00000000000000, 0.00000000000000, 0.00000000000000, 0.00000000000000, 0.00000000000000, 1.00000000000000],
])

assert np.allclose(TRANSITION_MATRIX.sum(axis=1), 1.0), \
    "Each row of TRANSITION_MATRIX must sum to 1.0"

DEFAULT_COL_IDX = RATING_LABELS.index("D")
PROB_DEFAULT_1Y = TRANSITION_MATRIX[:, DEFAULT_COL_IDX]
PROB_SOLVENT_1Y = 1 - PROB_DEFAULT_1Y
SOLVENT_DEFAULT_MATRIX = np.column_stack([PROB_SOLVENT_1Y, PROB_DEFAULT_1Y])

# Hypothetical example market data (user-supplied, not live market data).
# (tenor_years, risk_free_rate)
RATE_CURVE = [
    (0.08, 0.0086), (0.25, 0.0087), (0.50, 0.0089), (1.00, 0.0095),
    (2.00, 0.0118), (3.00, 0.0127), (4.00, 0.0147), (5.00, 0.0160),
]

# (tenor_years, spread_AAA_bps, AA, A, BBB, BB, B, CCC) — all in basis points
CREDIT_SPREADS = [
    (0.08, 10, 20, 30, 40, 50, 60, 70),
    (0.25, 20, 30, 40, 50, 60, 70, 80),
    (0.50, 40, 60, 80, 100, 120, 140, 160),
    (1.00, 50, 80, 100, 120, 150, 180, 200),
    (2.00, 80, 100, 120, 150, 180, 200, 250),
    (3.00, 100, 120, 140, 170, 200, 250, 300),
    (4.00, 150, 180, 200, 250, 270, 300, 350),
    (5.00, 200, 220, 260, 300, 350, 400, 450),
]


def build_spot_curve(rate_curve, credit_spreads):
    """Combine the risk-free curve with rating spreads into per-rating spot curves."""
    rate_dict = {r[0]: r[1] for r in rate_curve}
    spot_rating = []
    for row in credit_spreads:
        tenor = row[0]
        spreads_bps = row[1:]
        rf_rate = rate_dict[tenor]
        corp_spots = [rf_rate + (bps / 10000) for bps in spreads_bps]
        spot_rating.append(tuple([tenor] + corp_spots))
    return spot_rating


def get_probabilities_and_labels(rating, years_to_maturity):
    """
    Pick the right set of probabilities and labels based on remaining
    contract length.

    - years_to_maturity == 1: only 2 outcomes matter — Solvent or Default.
    - years_to_maturity > 1: use the full transition matrix (multi-rating
      outcomes). This single-period model reuses the 1-year transition
      probabilities directly as an approximation for the year-1 horizon —
      see repo README for the modeling caveat on multi-year contracts.
    """
    row_idx = RATING_LABELS.index(rating)
    if years_to_maturity == 1:
        return SOLVENT_DEFAULT_MATRIX[row_idx], ["S", "D"]
    return TRANSITION_MATRIX[row_idx], RATING_LABELS


def make_thresholds(probabilities):
    """Convert a rating's transition probabilities into Z-axis thresholds via inverse normal CDF."""
    cumulative_prob = np.cumsum(probabilities)
    thresholds = norm.ppf(cumulative_prob)
    thresholds[-1] = np.inf  # guard against floating-point drift dropping the tail
    return thresholds


def categorize(z, thresholds, labels):
    """Map each simulated Z value to its corresponding rating/label based on thresholds."""
    result = np.empty_like(z, dtype=object)
    lower_bound = -np.inf
    for label, upper_bound in zip(labels, thresholds):
        result[(z > lower_bound) & (z <= upper_bound)] = label
        lower_bound = upper_bound
    return result


def simulate_rating_outcomes(portfolio, n_simulations, seed=None):
    """
    Simulate correlated rating migrations for every firm in the portfolio
    using a single-factor Gaussian copula: Z_i = rho_i * M + sqrt(1 - rho_i^2) * eps_i.

    Returns a DataFrame of shape (n_simulations, n_firms) with each firm's
    simulated outcome label per path.
    """
    rng = np.random.default_rng(seed)
    n_firms = len(portfolio)

    market_factor = rng.normal(0, 1, (1, n_simulations))
    firm_specific_factor = rng.normal(0, 1, (n_firms, n_simulations))
    asset_correlations = np.array(
        [firm["asset_correlation"] for firm in portfolio]
    ).reshape(n_firms, 1)

    z = (asset_correlations * market_factor) + (
        np.sqrt(1 - asset_correlations ** 2) * firm_specific_factor
    )

    firm_outcomes = [None] * n_firms
    for i, firm in enumerate(portfolio):
        probabilities, labels = get_probabilities_and_labels(
            firm["rating"], firm["years_to_maturity"]
        )
        thresholds = make_thresholds(probabilities)
        firm_outcomes[i] = categorize(z[i], thresholds, labels)

    outcome_columns = [firm["name"] for firm in portfolio]
    return pd.DataFrame({col: firm_outcomes[i] for i, col in enumerate(outcome_columns)})


def get_forward_n_to_1(rating_start, spot_rating, n):
    """Interpolate the spot curve for `rating_start` and derive the 1-year forward rate from tenor n to n+1."""
    if rating_start not in RATING_LABELS:
        raise ValueError(f"Rating '{rating_start}' not found in RATING_LABELS")
    rating_idx = RATING_LABELS.index(rating_start)

    tenors = np.array([row[0] for row in spot_rating])
    spots = np.array([row[rating_idx + 1] for row in spot_rating])
    cs = CubicSpline(tenors, spots, bc_type="natural")

    rate_start = cs(n)
    rate_end = cs(n + 1)
    return float(((1 + rate_end) ** (n + 1)) / ((1 + rate_start) ** n) - 1)


def value_forward_1y(ead, rating_end, payments_per_year, years_to_maturity, coupon_rate, lgd, spot_rating):
    """
    Value a bond's remaining cash flows as of the 1-year horizon, given the
    firm's rating outcome at that horizon (or its LGD-adjusted recovery
    value if it defaulted).
    """
    if rating_end == "D":
        return ead * (1 - lgd)

    if payments_per_year == 0:
        r = get_forward_n_to_1(rating_end, spot_rating, years_to_maturity)
        return ead / (1 + r) ** (years_to_maturity - 1)

    scale_time_in_1y = int((years_to_maturity - 1) * payments_per_year + 1)
    final_time = scale_time_in_1y - 1
    total_pv = 0.0
    for i in range(scale_time_in_1y):
        t = i / payments_per_year
        r = get_forward_n_to_1(rating_end, spot_rating, t)
        coupon = ead * (coupon_rate / payments_per_year)
        cash_flow = ead + coupon if i == final_time else coupon
        total_pv += cash_flow / (1 + r) ** t
    return total_pv


def build_value_matrices(portfolio, spot_rating):
    """
    Build the (n_firms x n_ratings) matrix of 1-year-horizon bond values
    under every possible rating outcome, plus the "no migration" baseline
    matrix (i.e. value if the firm stays at its CURRENT rating), and the
    resulting loss matrix (baseline - outcome value).
    """
    n_firms = len(portfolio)
    n_ratings = len(RATING_LABELS)

    value_matrix_1y = np.zeros((n_firms, n_ratings))
    value_matrix_credit_begin = np.zeros((n_firms, n_ratings))

    for i, firm in enumerate(portfolio):
        for k in range(n_ratings):
            value_matrix_1y[i, k] = value_forward_1y(
                firm["ead"], RATING_LABELS[k], firm["payments_per_year"],
                firm["years_to_maturity"], firm["coupon_rate"], firm["LGD"], spot_rating,
            )
            # Baseline value if the firm had stayed at its ORIGINAL rating
            # (same value repeated across columns — used as the mark-to-market anchor).
            value_matrix_credit_begin[i, k] = value_forward_1y(
                firm["ead"], firm["rating"], firm["payments_per_year"],
                firm["years_to_maturity"], firm["coupon_rate"], firm["LGD"], spot_rating,
            )

    loss_matrix_1y = value_matrix_credit_begin - value_matrix_1y
    return value_matrix_1y, value_matrix_credit_begin, loss_matrix_1y


def compute_scenario_losses(portfolio, outcomes_df, loss_matrix_1y):
    """Map each simulated joint scenario to its total portfolio loss and empirical probability."""
    rating_to_idx = {rating: i for i, rating in enumerate(RATING_LABELS)}
    firm_current_ratings = [firm["rating"] for firm in portfolio]
    outcome_columns = [firm["name"] for firm in portfolio]

    joint_scenario = (
        "(" + outcomes_df[outcome_columns].astype(str).agg(",".join, axis=1) + ")"
    )
    scenario_probabilities = pd.Series(joint_scenario).value_counts(normalize=True)

    scenario_losses = {}
    for scenario_str in scenario_probabilities.index:
        scenario_tuple = scenario_str.strip("()").split(",")
        total_loss = 0.0
        for i, outcome in enumerate(scenario_tuple):
            actual_rating = firm_current_ratings[i] if outcome == "S" else outcome
            total_loss += loss_matrix_1y[i, rating_to_idx[actual_rating]]
        scenario_losses[scenario_str] = total_loss

    portfolio_loss_scenarios = pd.Series(scenario_losses)
    return scenario_probabilities, portfolio_loss_scenarios


def compute_credit_var(scenario_probabilities, portfolio_loss_scenarios, alpha=0.999):
    """
    Compute Credit VaR and Economic Capital at the given confidence level
    from the empirical scenario loss distribution.

    Parameters
    ----------
    alpha : float
        Confidence level, e.g. 0.99 or 0.999. Adjustable — this is a
        Monte Carlo empirical percentile, so it can be set to match the
        KMV model's alpha for direct comparison.
    """
    va_df = pd.DataFrame({
        "Probability": scenario_probabilities,
        "Loss": portfolio_loss_scenarios,
    })
    va_df = va_df.sort_values(by="Loss").reset_index()
    va_df["Cum_Prob"] = va_df["Probability"].cumsum()

    try:
        credit_var = va_df[va_df["Cum_Prob"] >= alpha]["Loss"].iloc[0]
    except IndexError:
        credit_var = va_df["Loss"].max()

    expected_loss = (va_df["Probability"] * va_df["Loss"]).sum()
    economic_capital = credit_var - expected_loss

    return {
        "alpha": alpha,
        "Credit VaR": credit_var,
        "Expected Loss": expected_loss,
        "Economic Capital": economic_capital,
        "detail_table": va_df,
    }


def run_full_model(portfolio=PORTFOLIO, n_simulations=N_SIMULATIONS, alpha=0.999, seed=None):
    """Convenience wrapper: run the full pipeline end to end and return the Credit VaR result dict."""
    spot_rating = build_spot_curve(RATE_CURVE, CREDIT_SPREADS)
    outcomes_df = simulate_rating_outcomes(portfolio, n_simulations, seed=seed)
    _, _, loss_matrix_1y = build_value_matrices(portfolio, spot_rating)
    scenario_probabilities, portfolio_loss_scenarios = compute_scenario_losses(
        portfolio, outcomes_df, loss_matrix_1y
    )
    return compute_credit_var(scenario_probabilities, portfolio_loss_scenarios, alpha=alpha)


if __name__ == "__main__":
    result = run_full_model(alpha=0.999)
    print(f"--- Credit VaR Calculation ---")
    print(f"Confidence Level (Alpha): {result['alpha']:.1%}")
    print(f"Credit VaR:               {result['Credit VaR']:,.2f}")
    print(f"Expected Loss (EL):       {result['Expected Loss']:,.2f}")
    print(f"Economic Capital (EC):    {result['Economic Capital']:,.2f}")
