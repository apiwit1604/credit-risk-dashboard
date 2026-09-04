"""
credit_var_ratings.py
======================
Portfolio Credit Value-at-Risk using a ratings-migration Monte Carlo
model in the CreditMetrics tradition.

Model idea
----------
1. SYSTEMATIC RISK. Every firm's (unobserved) asset-value index Z_i is
   driven by a shared market factor M plus firm-specific idiosyncratic
   noise:

       Z_i = rho_i * M + sqrt(1 - rho_i^2) * eps_i     (M, eps_i ~ N(0,1))

   >>> CONVENTION WARNING <<< This file uses rho_i directly as the
   market-factor loading (the "plain correlation coefficient"
   convention). This is DIFFERENT from kmv_montecarlo.py /
   basel_single_factor.py, whose `asset_correlation` / R is already
   squared (Z = sqrt(R)*M + sqrt(1-R)*eps). The two are related by
   R = rho^2. Do not compare or interchange correlation inputs across
   these modules without converting -- see docs/06_correlation_conventions.md.

2. RATING MIGRATION. Each firm's 1-year-ahead rating (or a simple
   Solvent/Default outcome, if its remaining maturity is exactly 1 year)
   is determined by mapping Z_i through inverse-normal thresholds built
   from that firm's row of the ratings transition matrix -- the standard
   CreditMetrics threshold-mapping technique.

3. REVALUATION. For every simulated *joint* rating scenario across the
   portfolio, each position is revalued as the present value of its
   remaining cash flows, discounted on the credit-spread curve of its
   NEW (migrated-to) rating. Loss = (value at original rating) -
   (value at the simulated rating).

4. AGGREGATION. The probability-weighted loss distribution across all
   simulated joint scenarios gives Credit VaR (a loss percentile),
   Expected Shortfall (mean loss beyond VaR), and Economic Capital
   (VaR - Expected Loss).

KNOWN LIMITATION -- multi-year contracts. `rating_transition_probabilities`
reuses the 1-YEAR transition matrix directly for positions with
`years_to_maturity > 1`, which only approximates the *true* N-year-ahead
transition distribution. The mathematically correct fix is the N-th
matrix power of the transition matrix, T^N (`transition_matrix_power`
below provides this) -- it is exposed here but NOT yet wired into the
simulation. Treat multi-year portfolio results as directional until this
is connected.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from scipy.linalg import fractional_matrix_power
from scipy.stats import norm

DEFAULT_RATING_LABELS = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]


# --------------------------------------------------------------------------
# Transition matrix utilities
# --------------------------------------------------------------------------

def validate_transition_matrix(matrix) -> None:
    matrix = np.asarray(matrix)
    if not np.allclose(matrix.sum(axis=1), 1.0):
        raise ValueError("Each row of the transition matrix must sum to 1.0")


def transition_matrix_power(matrix, years: float) -> np.ndarray:
    """N-year transition matrix T^N (or a fractional power, e.g. for a
    6-month horizon T^0.5), via `scipy.linalg.fractional_matrix_power`.
    Not yet wired into the main simulation -- see module limitation note.
    """
    return fractional_matrix_power(np.asarray(matrix), years)


def rating_transition_probabilities(rating, years_to_maturity, transition_matrix, rating_labels):
    """
    Returns (probabilities, outcome_labels) for one firm.
      * years_to_maturity == 1 -> collapsed to 2 outcomes: Solvent / Default
      * years_to_maturity > 1  -> full transition-matrix row (approximation,
        see module docstring)
    """
    row_idx = rating_labels.index(rating)
    default_idx = rating_labels.index("D")
    if years_to_maturity == 1:
        p_default = transition_matrix[row_idx, default_idx]
        return np.array([1 - p_default, p_default]), ["S", "D"]
    return transition_matrix[row_idx], rating_labels


def _thresholds_from_probabilities(probabilities) -> np.ndarray:
    cumulative = np.cumsum(probabilities)
    thresholds = norm.ppf(cumulative)
    thresholds[-1] = np.inf  # guard against float drift dropping the tail
    return thresholds


def _categorize(z: np.ndarray, thresholds: np.ndarray, labels) -> np.ndarray:
    result = np.empty_like(z, dtype=object)
    lower = -np.inf
    for label, upper in zip(labels, thresholds):
        result[(z > lower) & (z <= upper)] = label
        lower = upper
    return result


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------

def simulate_rating_outcomes(portfolio, transition_matrix, rating_labels, n_sims, rng) -> pd.DataFrame:
    """Single-factor Monte Carlo simulation of each firm's 1-year-ahead
    rating / solvency outcome. Returns an (n_sims x n_firms) DataFrame of
    outcome labels.
    """
    n_firms = len(portfolio)
    market_factor = rng.standard_normal(n_sims)
    idiosyncratic = rng.standard_normal((n_firms, n_sims))
    rho = np.array([firm["asset_correlation"] for firm in portfolio]).reshape(n_firms, 1)

    z = rho * market_factor + np.sqrt(1 - rho ** 2) * idiosyncratic

    outcomes = {}
    for i, firm in enumerate(portfolio):
        probs, labels = rating_transition_probabilities(
            firm["rating"], firm["years_to_maturity"], transition_matrix, rating_labels
        )
        thresholds = _thresholds_from_probabilities(probs)
        outcomes[firm["name"]] = _categorize(z[i], thresholds, labels)

    return pd.DataFrame(outcomes)


# --------------------------------------------------------------------------
# Revaluation
# --------------------------------------------------------------------------

def _forward_rate(rating_label, spot_curve_by_rating, n_years, rating_labels):
    """1-year forward rate starting at year N, for the given post-migration
    rating, via a natural cubic spline through that rating's credit-spread
    -adjusted spot curve.
    """
    if rating_label not in rating_labels:
        raise ValueError(f"Unknown rating '{rating_label}'")
    col = rating_labels.index(rating_label) + 1  # column 0 of each row is the tenor

    tenors = np.array([row[0] for row in spot_curve_by_rating])
    spots = np.array([row[col] for row in spot_curve_by_rating])
    spline = CubicSpline(tenors, spots, bc_type="natural")

    rate_start = spline(n_years)
    rate_end = spline(n_years + 1)
    return ((1 + rate_end) ** (n_years + 1)) / ((1 + rate_start) ** n_years) - 1


def value_bond_at_rating(ead, rating_at_horizon, payments_per_year, years_to_maturity,
                          coupon_rate, lgd, spot_curve_by_rating, rating_labels):
    """PV, one year from today, of a position's remaining cash flows,
    assuming it has migrated to `rating_at_horizon` (or defaulted: 'D')."""
    if rating_at_horizon == "D":
        return ead * (1 - lgd)

    if payments_per_year == 0:
        r = _forward_rate(rating_at_horizon, spot_curve_by_rating, years_to_maturity, rating_labels)
        return ead / (1 + r) ** (years_to_maturity - 1)

    n_remaining_payments = int((years_to_maturity - 1) * payments_per_year + 1)
    coupon = ead * (coupon_rate / payments_per_year)
    pv = 0.0
    for i in range(n_remaining_payments):
        t = i / payments_per_year
        r = _forward_rate(rating_at_horizon, spot_curve_by_rating, t, rating_labels)
        cash_flow = ead + coupon if i == n_remaining_payments - 1 else coupon
        pv += cash_flow / (1 + r) ** t
    return pv


# --------------------------------------------------------------------------
# Full pipeline
# --------------------------------------------------------------------------

@dataclass
class CreditVaRResult:
    scenario_probabilities: pd.Series
    scenario_losses: pd.Series
    detail_table: pd.DataFrame
    expected_loss: float
    credit_var: float
    expected_shortfall: float
    economic_capital: float
    alpha: float


def run_credit_var_ratings(portfolio, transition_matrix, rating_labels, spot_curve_by_rating,
                            n_sims: int = 200_000, alpha: float = 0.999,
                            random_seed: int | None = None) -> CreditVaRResult:
    transition_matrix = np.asarray(transition_matrix, dtype=float)
    validate_transition_matrix(transition_matrix)
    rng = np.random.default_rng(random_seed)

    outcomes_df = simulate_rating_outcomes(portfolio, transition_matrix, rating_labels, n_sims, rng)
    joint_scenario = "(" + outcomes_df.astype(str).agg(",".join, axis=1) + ")"
    scenario_probabilities = pd.Series(joint_scenario).value_counts(normalize=True)

    n_firms, n_ratings = len(portfolio), len(rating_labels)
    value_at_horizon = np.zeros((n_firms, n_ratings))
    value_at_start = np.zeros((n_firms, n_ratings))

    for i, firm in enumerate(portfolio):
        begin_value = value_bond_at_rating(
            firm["ead"], firm["rating"], firm["payments_per_year"],
            firm["years_to_maturity"], firm["coupon_rate"], firm["LGD"],
            spot_curve_by_rating, rating_labels,
        )
        value_at_start[i, :] = begin_value
        for k, rating in enumerate(rating_labels):
            value_at_horizon[i, k] = value_bond_at_rating(
                firm["ead"], rating, firm["payments_per_year"],
                firm["years_to_maturity"], firm["coupon_rate"], firm["LGD"],
                spot_curve_by_rating, rating_labels,
            )

    loss_matrix = value_at_start - value_at_horizon  # (n_firms x n_ratings)
    rating_to_idx = {r: i for i, r in enumerate(rating_labels)}
    firm_start_rating = [firm["rating"] for firm in portfolio]

    scenario_losses = {}
    for scenario_str in scenario_probabilities.index:
        outcomes = scenario_str.strip("()").split(",")
        total_loss = 0.0
        for i, outcome in enumerate(outcomes):
            rating = firm_start_rating[i] if outcome == "S" else outcome
            total_loss += loss_matrix[i, rating_to_idx[rating]]
        scenario_losses[scenario_str] = total_loss
    scenario_losses = pd.Series(scenario_losses)

    detail = pd.DataFrame({"Probability": scenario_probabilities, "Loss": scenario_losses})
    detail = detail.sort_values("Loss").reset_index().rename(columns={"index": "Scenario"})
    detail["Cumulative Probability"] = detail["Probability"].cumsum()

    try:
        credit_var = float(detail.loc[detail["Cumulative Probability"] >= alpha, "Loss"].iloc[0])
    except IndexError:
        credit_var = float(detail["Loss"].max())

    tail = detail[detail["Loss"] >= credit_var]
    expected_shortfall = float((tail["Loss"] * tail["Probability"]).sum() / tail["Probability"].sum())
    expected_loss = float((detail["Probability"] * detail["Loss"]).sum())
    economic_capital = credit_var - expected_loss

    return CreditVaRResult(
        scenario_probabilities=scenario_probabilities, scenario_losses=scenario_losses,
        detail_table=detail, expected_loss=expected_loss, credit_var=credit_var,
        expected_shortfall=expected_shortfall, economic_capital=economic_capital, alpha=alpha,
    )
