# -*- coding: utf-8 -*-
"""
Shared Streamlit session-state helpers so every page reads and writes the
*same* portfolio and model settings. This is the only file in `src/` that
imports Streamlit — everything else in this package is plain Python /
NumPy / pandas so it can be reused outside the dashboard (tests, notebooks,
a future API, etc.).
"""
from __future__ import annotations

import streamlit as st

from . import config


def init_state() -> None:
    """Populate st.session_state with defaults, without clobbering values
    the user already changed on another page. Call this at the top of
    every page.
    """
    defaults = {
        "rating_labels": list(config.DEFAULT_RATING_LABELS),
        "transition_matrix": config.DEFAULT_TRANSITION_MATRIX.copy(),
        "rf_data": list(config.DEFAULT_RF_DATA),
        "credit_spread_data": list(config.DEFAULT_CREDIT_SPREAD_DATA),
        "portfolio": [dict(f) for f in config.DEFAULT_PORTFOLIO],
        "loss_horizon": config.DEFAULT_LOSS_HORIZON,
        "n_sim_kmv": config.DEFAULT_N_SIM,
        "n_sim_creditmetrics": config.DEFAULT_N_SIM,
        "confidence_kmv": config.DEFAULT_CONFIDENCE_KMV,
        "confidence_creditmetrics": config.DEFAULT_CONFIDENCE_CREDITMETRICS,
        "basel_use_firm_maturity": True,
        "basel_maturity_override": 2.5,
        "kmv_seed": 42,
        "creditmetrics_seed": 42,
        # Model Comparison page (5) settings are intentionally independent of
        # Pages 2-4's own settings above — see the module docstring in
        # pages/5_🧮_Model_Comparison.py for why.
        "compare_loss_horizon": config.DEFAULT_LOSS_HORIZON,
        "compare_n_sims": config.DEFAULT_N_SIM,
        "compare_confidence": config.DEFAULT_CONFIDENCE_KMV,
        "compare_seed": 42,
        "compare_maturity": 2.5,
        # Bumped every time the Settings page reshapes the transition
        # matrix / credit-spread curve to a new rating scale, so their
        # data_editor widgets get a fresh key and don't try to replay an
        # old edit-diff against a differently-shaped table.
        "settings_version": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_settings_to_default() -> None:
    """Reset only the Settings-page values (rating scale, transition
    matrix, curves) — leaves the portfolio and per-model UI choices alone.
    """
    st.session_state["rating_labels"] = list(config.DEFAULT_RATING_LABELS)
    st.session_state["transition_matrix"] = config.DEFAULT_TRANSITION_MATRIX.copy()
    st.session_state["rf_data"] = list(config.DEFAULT_RF_DATA)
    st.session_state["credit_spread_data"] = list(config.DEFAULT_CREDIT_SPREAD_DATA)
