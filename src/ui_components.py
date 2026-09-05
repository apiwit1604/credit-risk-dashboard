# -*- coding: utf-8 -*-
"""Reusable Streamlit widgets shared by more than one page — mainly the
portfolio editor(s).

The master portfolio (st.session_state['portfolio']) always stores the
*full* Firm schema (every field any model might need), because the same
firm is shared across Pages 2-5. What differs page to page is which
columns are actually shown/editable:

  * Pages 2, 3, 4 each show only the fields *their own* model reads
    (`render_model_portfolio_editor`), so the table isn't cluttered with
    inputs that model ignores.
  * Page 5 shows every field at once (`render_full_portfolio_editor`),
    since the Comparison page runs all three models and is the natural
    place to see (or fix) the whole record — including a rename, which
    the restricted views don't handle by field-preservation (see the
    note in `render_model_portfolio_editor`).
"""
from __future__ import annotations

from typing import Dict, List

import pandas as pd
import streamlit as st

FULL_PORTFOLIO_COLUMNS: List[str] = [
    "name", "rating", "years_to_maturity", "asset_correlation", "asset_value",
    "ead", "asset_mean", "asset_std", "coupon_rate", "payments_per_year", "lgd",
]

# Exactly the fields each model reads — nothing more. See src/credit_var/*.py.
MODEL_COLUMNS: Dict[str, List[str]] = {
    "kmv": ["name", "asset_correlation", "asset_value", "ead", "asset_mean", "asset_std", "lgd"],
    "creditmetrics": ["name", "rating", "asset_correlation", "years_to_maturity", "ead", "coupon_rate", "payments_per_year", "lgd"],
    "basel": ["name", "rating", "ead", "lgd"],
}

# Used to fill in fields a restricted view doesn't show, for a firm that's
# brand new (added from that view) or has never been touched anywhere else.
FIELD_DEFAULTS: Dict[str, object] = {
    "name": "New_Firm",
    "rating": "BBB",
    "years_to_maturity": 1.0,
    "asset_correlation": 0.50,
    "asset_value": 100.0,
    "ead": 100.0,
    "asset_mean": 0.08,
    "asset_std": 0.50,
    "coupon_rate": 0.05,
    "payments_per_year": 2,
    "lgd": 0.45,
}

COLUMN_LABELS = {
    "name": "Firm", "rating": "Rating", "years_to_maturity": "Maturity (yrs)",
    "asset_correlation": "Asset Corr. (ρ)", "asset_value": "Asset Value (V0)", "ead": "EAD",
    "asset_mean": "Asset Drift (μ)", "asset_std": "Asset Vol (σ)", "coupon_rate": "Coupon Rate",
    "payments_per_year": "Payments/Yr", "lgd": "LGD",
}

COLUMN_HELP = {
    "name": "Firm / exposure identifier — shared key across every page's view of the portfolio.",
    "rating": "Current credit rating.",
    "years_to_maturity": "Remaining life of the exposure, in years.",
    "asset_correlation": "R² loading on the common systematic factor (single-factor Gaussian copula), 0-0.99.",
    "asset_value": "Current market value of the firm's assets (V0).",
    "ead": "Exposure at Default.",
    "asset_mean": "Annualised expected asset return (drift).",
    "asset_std": "Annualised asset return volatility.",
    "coupon_rate": "Annual coupon rate on the exposure (0 for a zero-coupon loan).",
    "payments_per_year": "Coupon frequency per year (0 for a zero-coupon / bullet instrument).",
    "lgd": "Loss Given Default, as a fraction of EAD (0-1).",
}


def _column_config(col: str, rating_choices: List[str]):
    label, help_text = COLUMN_LABELS[col], COLUMN_HELP[col]
    if col == "name":
        return st.column_config.TextColumn(label, required=True, help=help_text)
    if col == "rating":
        return st.column_config.SelectboxColumn(label, options=rating_choices, required=True, help=help_text)
    if col == "asset_correlation":
        return st.column_config.NumberColumn(label, min_value=0.0, max_value=0.99, step=0.01, help=help_text)
    if col == "years_to_maturity":
        return st.column_config.NumberColumn(label, min_value=0.08, step=0.25, help=help_text)
    if col in ("asset_value", "ead"):
        return st.column_config.NumberColumn(label, min_value=0.01, help=help_text)
    if col in ("asset_mean", "asset_std", "coupon_rate"):
        min_value = 0.001 if col == "asset_std" else None
        return st.column_config.NumberColumn(label, min_value=min_value, step=0.01, format="%.4f", help=help_text)
    if col == "payments_per_year":
        return st.column_config.NumberColumn(label, min_value=0, step=1, help=help_text)
    if col == "lgd":
        return st.column_config.NumberColumn(label, min_value=0.0, max_value=1.0, step=0.01, help=help_text)
    raise KeyError(col)


def render_full_portfolio_editor(key: str = "portfolio_editor_full", caption: str = "") -> pd.DataFrame:
    """Every field, for the Comparison page. Overwrites the master
    portfolio wholesale — safe here because nothing is hidden.
    """
    rating_choices = [r for r in st.session_state["rating_labels"] if r != "D"]
    df = pd.DataFrame(st.session_state["portfolio"])
    for col in FULL_PORTFOLIO_COLUMNS:
        if col not in df.columns:
            df[col] = FIELD_DEFAULTS[col]
    df = df[FULL_PORTFOLIO_COLUMNS]

    if caption:
        st.caption(caption)

    edited = st.data_editor(
        df, key=key, num_rows="dynamic", width="stretch",
        column_config={col: _column_config(col, rating_choices) for col in FULL_PORTFOLIO_COLUMNS},
    )
    cleaned = edited.dropna(subset=["name", "rating"])
    cleaned = cleaned[cleaned["name"].astype(str).str.strip() != ""]
    st.session_state["portfolio"] = cleaned.to_dict("records")
    return cleaned


def render_model_portfolio_editor(model_key: str, key: str, caption: str = "") -> pd.DataFrame:
    """Only the fields `model_key`'s model actually reads (see
    `MODEL_COLUMNS`). Edits are merged back into the master portfolio by
    firm name, so fields *not* shown here (e.g. a firm's rating, when
    editing the KMV view) are preserved rather than overwritten.

    Note: renaming a firm from a restricted view can't preserve its
    hidden fields (there's no old name left in the edited table to match
    against), so it resets them to defaults — rename firms from the
    Model Comparison page instead, where every field is visible.
    """
    columns = MODEL_COLUMNS[model_key]
    rating_choices = [r for r in st.session_state["rating_labels"] if r != "D"]
    master = st.session_state["portfolio"]

    rows = [{col: firm.get(col, FIELD_DEFAULTS[col]) for col in columns} for firm in master]
    df = pd.DataFrame(rows, columns=columns)

    if caption:
        st.caption(caption)

    edited = st.data_editor(
        df, key=key, num_rows="dynamic", width="stretch",
        column_config={col: _column_config(col, rating_choices) for col in columns},
    )
    edited = edited.dropna(subset=["name"])
    edited = edited[edited["name"].astype(str).str.strip() != ""]

    master_by_name = {firm["name"]: firm for firm in master}
    new_master = []
    for _, row in edited.iterrows():
        name = row["name"]
        base = {**FIELD_DEFAULTS, **master_by_name.get(name, {})}
        for col in columns:
            base[col] = row[col]
        base["name"] = name
        new_master.append(base)

    st.session_state["portfolio"] = new_master
    return edited
