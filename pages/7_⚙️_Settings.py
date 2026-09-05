# -*- coding: utf-8 -*-
"""Page 7 — Settings: the market/model inputs that are hard to eyeball.

Everything here is intentionally *not* firm-specific (that's the shared
portfolio editor on Pages 2-5) — this page controls the rating scale, the
transition matrix, and the two interest-rate curves that feed Pages 2-6.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from src import config
from src.state import init_state, reset_settings_to_default

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
init_state()

st.title("⚙️ Settings — Global Model Inputs")
st.caption(
    "Changes here apply the moment you click **Apply**, and immediately affect "
    "Pages 2-6 (any page that reads the transition matrix or the rate curves)."
)

if st.button("↩️ Reset everything on this page to default (ThaiBMA)"):
    reset_settings_to_default()
    st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Rating scale
# ---------------------------------------------------------------------------
st.subheader("1. Rating scale")
st.caption(
    "Renaming a label is safe. Changing *how many* ratings there are requires the "
    "transition matrix below to be resized to match — do both together, then Apply."
)
rating_labels_df = pd.DataFrame({"Rating": st.session_state["rating_labels"]})
edited_ratings = st.data_editor(
    rating_labels_df, num_rows="dynamic", width="stretch", key="rating_labels_editor",
    hide_index=True,
)
new_rating_labels = [r for r in edited_ratings["Rating"].tolist() if isinstance(r, str) and r.strip()]

st.divider()

# ---------------------------------------------------------------------------
# Transition matrix
# ---------------------------------------------------------------------------
st.subheader("2. 1-year rating transition matrix")
st.caption("Each row must sum to 1 (a probability distribution over ending ratings). Last row must be an absorbing default state.")

current_matrix = st.session_state["transition_matrix"]
current_labels = st.session_state["rating_labels"]
matrix_df = pd.DataFrame(current_matrix, index=current_labels, columns=current_labels)
edited_matrix_df = st.data_editor(matrix_df, width="stretch", key="transition_matrix_editor")

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
    st.success("All rows sum to 1. ✅")

st.divider()

# ---------------------------------------------------------------------------
# Risk-free curve & credit spread curve
# ---------------------------------------------------------------------------
st.subheader("3. Risk-free curve")
rf_df = pd.DataFrame(st.session_state["rf_data"], columns=["Tenor (yrs)", "Risk-free rate"])
edited_rf = st.data_editor(rf_df, num_rows="dynamic", width="stretch", key="rf_data_editor", hide_index=True)

st.subheader("4. Credit-spread curve (basis points over risk-free)")
st.caption(
    "Tenor grid must exactly match the risk-free curve above. Columns are every rating "
    "except the default state — currently: " + ", ".join([r for r in new_rating_labels if r != "D"])
)
non_default = [r for r in current_labels if r != "D"]
spread_cols = ["Tenor (yrs)"] + non_default
spread_rows = []
for row in st.session_state["credit_spread_data"]:
    spread_rows.append(dict(zip(spread_cols, row)))
spread_df = pd.DataFrame(spread_rows)
edited_spread = st.data_editor(spread_df, num_rows="dynamic", width="stretch", key="credit_spread_editor", hide_index=True)

st.divider()

if st.button("✅ Apply settings", type="primary"):
    errors = []

    if len(new_rating_labels) < 2 or new_rating_labels[-1] != "D":
        errors.append("The last rating label must be 'D' (the absorbing default state).")
    if len(new_rating_labels) != edited_matrix_df.shape[0]:
        errors.append(
            f"Rating scale has {len(new_rating_labels)} entries but the transition matrix has "
            f"{edited_matrix_df.shape[0]} rows — resize the matrix to match before applying."
        )

    rf_tenors = edited_rf["Tenor (yrs)"].tolist()
    spread_tenors = edited_spread["Tenor (yrs)"].tolist()
    if rf_tenors != spread_tenors:
        errors.append("The risk-free curve and credit-spread curve must use the same tenor grid (same years, same order).")
    if len(non_default) != edited_spread.shape[1] - 1:
        errors.append("The credit-spread table needs exactly one column per non-default rating.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        matrix_values = edited_matrix_df.to_numpy(dtype=float)
        if normalize:
            matrix_values = matrix_values / matrix_values.sum(axis=1, keepdims=True)

        st.session_state["rating_labels"] = new_rating_labels
        st.session_state["transition_matrix"] = matrix_values
        st.session_state["rf_data"] = list(edited_rf.itertuples(index=False, name=None))
        st.session_state["credit_spread_data"] = [tuple(row) for row in edited_spread.itertuples(index=False, name=None)]

        st.cache_data.clear()
        st.success("Settings applied — Pages 2-6 will use these values now.")

with st.expander("🔄 Restore ThaiBMA defaults for reference"):
    st.write("Rating labels:", config.DEFAULT_RATING_LABELS)
    st.dataframe(pd.DataFrame(config.DEFAULT_TRANSITION_MATRIX, index=config.DEFAULT_RATING_LABELS, columns=config.DEFAULT_RATING_LABELS).style.format("{:.4%}"))
    st.dataframe(pd.DataFrame(config.DEFAULT_RF_DATA, columns=["Tenor (yrs)", "Risk-free rate"]))
    st.dataframe(pd.DataFrame(config.DEFAULT_CREDIT_SPREAD_DATA, columns=["Tenor (yrs)"] + config.DEFAULT_RATING_LABELS[:-1]))
