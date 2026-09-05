# -*- coding: utf-8 -*-
"""
CreditMetrics-style rating-migration Monte Carlo model for portfolio
Credit VaR: firms are re-valued under every possible future rating (via
`valuation.value_forward`); simulated migration outcomes are drawn from a
single-factor Gaussian copula on thresholds implied by the transition
matrix; portfolio loss is aggregated across the simulated draws.
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import norm

from ..valuation import calculate_credit_loss


def get_probabilities_and_labels(
    rating: str,
    years_to_maturity: float,
    loss_horizon: float,
    rating_labels: Sequence[str],
    transition_matrix_n: pd.DataFrame,
) -> Tuple[np.ndarray, List[str]]:
    """Pick the right probability vector for one firm: the full migration
    row if the exposure survives past the horizon, or a simple
    solvent/default split if it matures within the horizon.
    """
    rating_labels = list(rating_labels)
    row_idx = rating_labels.index(rating)
    if years_to_maturity <= loss_horizon:
        prob_default = transition_matrix_n["D"].values[row_idx]
        return np.array([1 - prob_default, prob_default]), ["S", "D"]
    return transition_matrix_n.iloc[row_idx].values, rating_labels


def make_thresholds(probabilities: np.ndarray) -> np.ndarray:
    cumulative = np.cumsum(probabilities)
    thresholds = norm.ppf(cumulative)
    thresholds[-1] = np.inf
    return thresholds


def categorize(z: np.ndarray, thresholds: np.ndarray, labels: Sequence[str]) -> np.ndarray:
    result = np.empty_like(z, dtype=object)
    lower_bound = -np.inf
    for label, upper_bound in zip(labels, thresholds):
        mask = (z > lower_bound) & (z <= upper_bound)
        result[mask] = label
        lower_bound = upper_bound
    return result


def calculate_credit_var(
    portfolio: Sequence[dict],
    transition_matrix_n: pd.DataFrame,
    rating_labels: Sequence[str],
    spot_rating: pd.DataFrame,
    loss_horizon: float,
    confidence_level: float = 0.999,
    n_simulations: int = 200_000,
    random_seed: int = 42,
) -> dict:
    rating_labels = list(rating_labels)
    rng = np.random.default_rng(random_seed)
    n_firms = len(portfolio)

    market_factor = rng.standard_normal((1, n_simulations))
    firm_specific_factor = rng.standard_normal((n_firms, n_simulations))
    asset_correlations = np.array([f["asset_correlation"] for f in portfolio]).reshape(n_firms, 1)

    z = asset_correlations * market_factor + np.sqrt(1 - asset_correlations ** 2) * firm_specific_factor

    firm_outcomes = []
    for i, firm in enumerate(portfolio):
        probabilities, labels = get_probabilities_and_labels(
            firm["rating"], firm["years_to_maturity"], loss_horizon, rating_labels, transition_matrix_n,
        )
        thresholds = make_thresholds(probabilities)
        firm_outcomes.append(categorize(z[i], thresholds, labels))

    outcome_columns = [f["name"] for f in portfolio]
    outcomes_df = pd.DataFrame({col: firm_outcomes[i] for i, col in enumerate(outcome_columns)})

    value_matrix_n, _, loss_table = calculate_credit_loss(portfolio, rating_labels, loss_horizon, spot_rating)
    rating_to_idx = {rating: i for i, rating in enumerate(rating_labels)}
    current_ratings = [f["rating"] for f in portfolio]

    loss_per_firm_sim = np.zeros((n_firms, n_simulations))
    for i in range(n_firms):
        firm_labels = outcomes_df[outcome_columns[i]].values
        actual_ratings = np.where(firm_labels == "S", current_ratings[i], firm_labels)
        indices = [rating_to_idx[r] for r in actual_ratings]
        loss_per_firm_sim[i] = loss_table[i, indices]

    total_losses = loss_per_firm_sim.sum(axis=0)

    expected_loss = float(total_losses.mean())
    var = float(np.percentile(total_losses, confidence_level * 100))
    expected_shortfall = float(total_losses[total_losses >= var].mean())
    economic_capital = var - expected_loss

    # --- Performance fix vs. the original notebook ----------------------
    # `.astype(str).agg(",".join, axis=1)` runs a Python-level function
    # call *per simulation row*. With n_firms columns that's cheap when
    # n_firms is small, but the per-row Python overhead still dominates at
    # a few hundred thousand rows. Building the joined string column-by-
    # column instead keeps every step vectorized (pandas' native string
    # ops), since the loop below runs over `n_firms` columns, not over
    # `n_simulations` rows.
    joint_scenario = outcomes_df[outcome_columns[0]].astype(str)
    for col in outcome_columns[1:]:
        joint_scenario = joint_scenario + "," + outcomes_df[col].astype(str)
    joint_scenario = "(" + joint_scenario + ")"
    summary = pd.DataFrame({"Scenario": joint_scenario, "Loss": total_losses})
    event_summary = (
        summary.groupby("Scenario")
        .agg(Count=("Loss", "count"), Loss_Amount=("Loss", "first"))
        .reset_index()
    )
    event_summary["Probability"] = event_summary["Count"] / n_simulations
    event_summary = event_summary.sort_values("Loss_Amount", ascending=False).reset_index(drop=True)

    return {
        "expected_loss": expected_loss,
        "var": var,
        "expected_shortfall": expected_shortfall,
        "economic_capital": economic_capital,
        "event_summary": event_summary,
        "total_losses": total_losses,
    }
