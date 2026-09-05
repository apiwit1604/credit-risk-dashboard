# -*- coding: utf-8 -*-
"""Streamlit-cached wrappers around the pure `src` model functions, so
identical inputs (same portfolio, same settings) aren't recomputed on
every script rerun triggered by an unrelated widget elsewhere on the page.
"""
from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd
import streamlit as st

from .credit_var.basel_single_factor import run_single_factor_basel
from .credit_var.credit_metrics import calculate_credit_var
from .credit_var.merton_kmv import run_kmv_simulation
from .curves import build_spot_curves, build_transition_matrix_n


@st.cache_data(show_spinner=False)
def cached_transition_matrix_n(transition_matrix, rating_labels: Sequence[str], loss_horizon: float) -> pd.DataFrame:
    return build_transition_matrix_n(transition_matrix, rating_labels, loss_horizon)


@st.cache_data(show_spinner=False)
def cached_spot_curves(rf_data, credit_spread_data, rating_labels: Sequence[str]):
    return build_spot_curves(rf_data, credit_spread_data, rating_labels)


@st.cache_data(show_spinner="Running Merton–KMV Monte Carlo simulation…")
def cached_kmv(portfolio, loss_horizon: float, n_sims: int, confidence_level: float, seed: int) -> dict:
    return run_kmv_simulation(portfolio, loss_horizon, n_sims, confidence_level, seed)


@st.cache_data(show_spinner="Running CreditMetrics Monte Carlo simulation…")
def cached_credit_metrics(
    portfolio, transition_matrix_n, rating_labels: Sequence[str], spot_rating,
    loss_horizon: float, confidence_level: float, n_simulations: int, seed: int,
) -> dict:
    return calculate_credit_var(
        portfolio, transition_matrix_n, rating_labels, spot_rating,
        loss_horizon, confidence_level, n_simulations, seed,
    )


@st.cache_data(show_spinner=False)
def cached_basel(portfolio, transition_matrix_n, maturity_override: Optional[float], confidence_level: float) -> dict:
    return run_single_factor_basel(portfolio, transition_matrix_n, maturity_override, confidence)
