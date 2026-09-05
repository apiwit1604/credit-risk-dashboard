# -*- coding: utf-8 -*-
"""Page 7 — Settings: the market/model inputs that are hard to eyeball.

The Rating scale section is deliberately two-step:

  1. Edit the rating list however you like (add/remove/rename/reorder),
     then click **Confirm rating scale**. That immediately reshapes the
     transition matrix (both row and column headers) and the
     credit-spread curve (column headers) to match — carrying over data
     for ratings that still exist, and filling in neutral defaults for
     anything brand new. Everything else on this page is untouched.
  2. Fine-tune the actual numbers (transition probabilities, spread bps,
     risk-free curve) in the tables below, then click **Apply settings**
     to commit those values.

Splitting it this way means changing *which* ratings exist doesn't get
tangled up with editing the *values* in an already-shaped table.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src import config
from src.rating_scale import DEFAULT_NEW_RATING_SPREAD_BPS, confirm_rating_scale
from src.state import init_state, reset_settings_to_default

st.set_page_config(page_title="Settings", layout="wide")
init_state()

# ==========================================
# HIDE STREAMLIT DEFAULT NAVIGATION
# ==========================================
st.markdown(
    """
    <style>
        /* ซ่อน Default Multi-page Navigation ด้านบน Sidebar */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# CUSTOM SIDEBAR DESIGN
# ==========================================
with st.sidebar:
    st.markdown("## Risk Analytics")
    st.caption("Portfolio Credit Risk Suite v1.0")
    st.divider()

    # หน้าหลัก
    st.page_link("app.py", label="Overview & Introduction")
    
    st.divider()

    # Section 1: Core Models
    st.caption("MODELING FRAMEWORKS")
    st.page_link("pages/2_Merton_KMV_CVaR.py", label="Merton–KMV CVaR")
    st.page_link("pages/3_CreditMetrics_CVaR.py", label="CreditMetrics CVaR")
    st.page_link("pages/4_Basel_Single_Factor_CVaR.py", label="Basel Single Factor Credit VaR")

    st.divider()

    # Section 2: Analytics & Calibration
    st.caption("ANALYTICS & PARAMETERS")
    st.page_link("pages/5_Model_Comparison.py", label="Model Comparison")
    st.page_link("pages/6_Probability_of_Default.py", label="Probability of Default")

    st.divider()

    # Section 3: Configuration
    st.caption("SYSTEM CONFIGURATION")
    st.page_link("pages/7_Settings.py", label="Settings")

    # Bottom Widget: Summary Panel
    st.divider()
    with st.container():
        st.caption("PORTFOLIO STATE")
        st.markdown("**Shared State:** Active")
        st.caption("Changes in portfolio data or settings will sync dynamically across all pages.")

    st.divider()
    # ==========================================
    # CREDITS & LICENSE
    # ==========================================
    st.caption("DEVELOPER & LICENSE")
    st.markdown("**Developed by:** Apiwit Oonworg")
    st.caption("© 2026 Apiwit Oonworg. All rights reserved.")

st.title("Settings — Global Model Inputs")
st.caption(
    "Confirming the rating scale below applies immediately. Everything else needs "
    "**Apply settings** at the bottom. Both immediately affect Pages (Merton KMV CVaR, CreditMetrics CVaR,Basel Single-Factor CVaR, Model Comparison and Probability of Default)."
)

if st.button("Reset everything on this page to default (ThaiBMA)"):
    reset_settings_to_default()
    st.session_state["settings_version"] += 1
    st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# 1. Rating scale — edit freely, then Confirm to reshape the matrix/curve
# ---------------------------------------------------------------------------
st.subheader("1. Rating scale")
st.caption(
    "Add, remove, rename, or reorder ratings however you like — the last one must stay "
    "the absorbing default state (\"D\"). Click **Confirm rating scale** to carry the "
    "transition matrix and credit-spread curve over to this new scale."
)

version = st.session_state["settings_version"]
rating_labels_df = pd.DataFrame({"Rating": st.session_state["rating_labels"]})
edited_ratings = st.data_editor(
    rating_labels_df, num_rows="dynamic", width="stretch",
    key=f"rating_labels_editor_v{version}", hide_index=True,
)
draft_rating_labels = [r.strip() for r in edited_ratings["Rating"].tolist() if isinstance(r, str) and r.strip()]

if st.button("Confirm rating scale", type="primary"):
    old_labels = list(st.session_state["rating_labels"])
    errors = confirm_rating_scale(draft_rating_labels, st.session_state)

    if errors:
        for e in errors:
            st.error(e)
    else:
        st.session_state["settings_version"] += 1
        st.cache_data.clear()

        new_labels = st.session_state["rating_labels"]
        added = [r for r in new_labels if r not in old_labels]
        removed = [r for r in old_labels if r not in new_labels]
        msg = "Rating scale confirmed — matrix and credit-spread curve reshaped to match."
        if added:
            msg += f" New rating(s) **{', '.join(added)}** default to a neutral 100%-stays-put row " \
                   f"and a flat {DEFAULT_NEW_RATING_SPREAD_BPS:.0f}bp placeholder spread — edit those below."
        if removed:
            msg += f" Removed: **{', '.join(removed)}**. Surviving rows may no longer sum to 1 — check the warning below."
        st.success(msg)
        st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# 2. Transition matrix — values only; shape now follows the confirmed scale
# ---------------------------------------------------------------------------
version = st.session_state["settings_version"]  # re-read in case Confirm just bumped it
current_labels = st.session_state["rating_labels"]
non_default_labels = [r for r in current_labels if r != "D"]

st.subheader("2. 1-year rating transition matrix")
st.caption("Each row must sum to 1 (a probability distribution over ending ratings). Last row must be an absorbing default state.")

current_matrix = st.session_state["transition_matrix"]
matrix_df = pd.DataFrame(current_matrix, index=current_labels, columns=current_labels)
edited_matrix_df = st.data_editor(matrix_df, width="stretch", key=f"transition_matrix_editor_v{version}")

row_sums = edited_matrix_df.sum(axis=1)
off_by = (row_sums - 1.0).abs()
if (off_by > 1e-6).any():
    bad_rows = row_sums[off_by > 1e-6]
    st.warning(
        "These rows don't sum to 1 yet — normalize them (or fix by hand) before applying:\n\n"
        + "\n".join(f"- **{idx}**: sums to {val:.6f}" for idx, val in bad_rows.items())
    )
    normalize = st.checkbox("Auto-normalize every row to sum to 1 when I click Apply", value=True)
else:
    normalize = False
    st.success("All rows sum to 1.")

st.divider()

# ---------------------------------------------------------------------------
# 3. Risk-free curve & 4. credit-spread curve — values only
# ---------------------------------------------------------------------------
st.subheader("3. Risk-free curve")
rf_df = pd.DataFrame(st.session_state["rf_data"], columns=["Tenor (yrs)", "Risk-free rate"])
edited_rf = st.data_editor(rf_df, num_rows="dynamic", width="stretch", key="rf_data_editor", hide_index=True)

st.subheader("4. Credit-spread curve (basis points over risk-free)")
st.caption(
    "Tenor grid must exactly match the risk-free curve above. Columns follow the "
    "confirmed rating scale — currently: " + ", ".join(non_default_labels)
)
spread_cols = ["Tenor (yrs)"] + non_default_labels
spread_rows = [dict(zip(spread_cols, row)) for row in st.session_state["credit_spread_data"]]
spread_df = pd.DataFrame(spread_rows, columns=spread_cols)
edited_spread = st.data_editor(
    spread_df, num_rows="dynamic", width="stretch",
    key=f"credit_spread_editor_v{version}", hide_index=True,
)

st.divider()

if st.button("Apply settings", type="primary"):
    errors = []

    if len(current_labels) != edited_matrix_df.shape[0]:
        errors.append(
            "The transition matrix no longer matches the rating scale — click "
            "**Confirm rating scale** above first, then re-check the values here."
        )

    rf_tenors = edited_rf["Tenor (yrs)"].tolist()
    spread_tenors = edited_spread["Tenor (yrs)"].tolist()
    if rf_tenors != spread_tenors:
        errors.append("The risk-free curve and credit-spread curve must use the same tenor grid (same years, same order).")
    if len(non_default_labels) != edited_spread.shape[1] - 1:
        errors.append(
            "The credit-spread table's columns no longer match the rating scale — click "
            "**Confirm rating scale** above first, then re-check the values here."
        )

    if errors:
        for e in errors:
            st.error(e)
    else:
        matrix_values = edited_matrix_df.to_numpy(dtype=float)
        if normalize:
            matrix_values = matrix_values / matrix_values.sum(axis=1, keepdims=True)

        st.session_state["transition_matrix"] = matrix_values
        st.session_state["rf_data"] = list(edited_rf.itertuples(index=False, name=None))
        st.session_state["credit_spread_data"] = [tuple(row) for row in edited_spread.itertuples(index=False, name=None)]

        st.cache_data.clear()
        st.success("Settings applied — Pages 2-6 will use these values now.")

with st.expander("Restore ThaiBMA defaults for reference"):
    st.write("Rating labels:", config.DEFAULT_RATING_LABELS)
    st.dataframe(pd.DataFrame(config.DEFAULT_TRANSITION_MATRIX, index=config.DEFAULT_RATING_LABELS, columns=config.DEFAULT_RATING_LABELS).style.format("{:.4%}"))
    st.dataframe(pd.DataFrame(config.DEFAULT_RF_DATA, columns=["Tenor (yrs)", "Risk-free rate"]))
    st.dataframe(pd.DataFrame(config.DEFAULT_CREDIT_SPREAD_DATA, columns=["Tenor (yrs)"] + config.DEFAULT_RATING_LABELS[:-1]))
