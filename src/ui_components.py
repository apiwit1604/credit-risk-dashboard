# -*- coding: utf-8 -*-
"""Reusable Streamlit widgets shared by more than one page — mainly the
portfolio editor, so that editing the book on any one of pages 2-5 keeps
every other page in sync (all backed by the same st.session_state key)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

PORTFOLIO_COLUMNS = [
    "name", "rating", "years_to_maturity", "asset_correlation", "asset_value",
    "ead", "asset_mean", "asset_std", "coupon_rate", "payments_per_year", "lgd",
]

PORTFOLIO_HELP = {
    "name": "Firm / exposure identifier.",
    "rating": "Current credit rating (drives both the KMV correlation-only view and the CreditMetrics / Basel PD).",
    "years_to_maturity": "Remaining life of the exposure, in years.",
    "asset_correlation": "R² loading on the common systematic factor (single-factor Gaussian copula), 0-0.99.",
    "asset_value": "Current market value of the firm's assets (V0).",
    "ead": "Exposure at Default — used as the simplified default barrier in KMV and as face value in the valuation model.",
    "asset_mean": "Annualised expected asset return (drift), used only by the Merton-KMV simulation.",
    "asset_std": "Annualised asset return volatility, used only by the Merton-KMV simulation.",
    "coupon_rate": "Annual coupon rate on the exposure (0 for a zero-coupon loan).",
    "payments_per_year": "Coupon frequency per year (0 for a zero-coupon / bullet instrument).",
    "lgd": "Loss Given Default, as a fraction of EAD (0-1).",
}


def render_portfolio_editor(key: str = "portfolio_editor", caption: str = "") -> pd.DataFrame:
    """Render the shared, editable portfolio table and write any edits
    straight back to st.session_state['portfolio']. Returns the resulting
    DataFrame for immediate use on the calling page.
    """
    rating_choices = [r for r in st.session_state["rating_labels"] if r != "D"]
    df = pd.DataFrame(st.session_state["portfolio"])
    for col in PORTFOLIO_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[PORTFOLIO_COLUMNS]

    if caption:
        st.caption(caption)

    edited = st.data_editor(
        df,
        key=key,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "name": st.column_config.TextColumn("Firm", required=True, help=PORTFOLIO_HELP["name"]),
            "rating": st.column_config.SelectboxColumn("Rating", options=rating_choices, required=True, help=PORTFOLIO_HELP["rating"]),
            "years_to_maturity": st.column_config.NumberColumn("Maturity (yrs)", min_value=0.08, step=0.25, help=PORTFOLIO_HELP["years_to_maturity"]),
            "asset_correlation": st.column_config.NumberColumn("Asset Corr. (ρ)", min_value=0.0, max_value=0.99, step=0.01, help=PORTFOLIO_HELP["asset_correlation"]),
            "asset_value": st.column_config.NumberColumn("Asset Value (V0)", min_value=0.01, help=PORTFOLIO_HELP["asset_value"]),
            "ead": st.column_config.NumberColumn("EAD", min_value=0.01, help=PORTFOLIO_HELP["ead"]),
            "asset_mean": st.column_config.NumberColumn("Asset Drift (μ)", step=0.01, format="%.4f", help=PORTFOLIO_HELP["asset_mean"]),
            "asset_std": st.column_config.NumberColumn("Asset Vol (σ)", min_value=0.001, step=0.01, format="%.4f", help=PORTFOLIO_HELP["asset_std"]),
            "coupon_rate": st.column_config.NumberColumn("Coupon Rate", min_value=0.0, step=0.005, format="%.4f", help=PORTFOLIO_HELP["coupon_rate"]),
            "payments_per_year": st.column_config.NumberColumn("Payments/Yr", min_value=0, step=1, help=PORTFOLIO_HELP["payments_per_year"]),
            "lgd": st.column_config.NumberColumn("LGD", min_value=0.0, max_value=1.0, step=0.01, help=PORTFOLIO_HELP["lgd"]),
        },
    )
    cleaned = edited.dropna(subset=["name", "rating"])
    st.session_state["portfolio"] = cleaned.to_dict("records")
    return cleaned
