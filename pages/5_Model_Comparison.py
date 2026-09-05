# -*- coding: utf-8 -*-
"""Page 5 — Side-by-side comparison of the three Credit VaR models."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.compute import (
    cached_basel,
    cached_credit_metrics,
    cached_kmv,
    cached_spot_curves,
    cached_transition_matrix_n,
)
from src.state import init_state
from src.ui_components import render_portfolio_editor

st.set_page_config(page_title="Credit VaR Model Comparison", layout="wide")
init_state()

st.title("Credit VaR Model Comparison")
st.caption(
    "Runs the same portfolio through Merton–KMV, CreditMetrics, and Basel Single-Factor, "
    "using the simulation settings already chosen on Pages 2–4."
)

st.subheader("Portfolio")
render_portfolio_editor(key="portfolio_editor_compare", caption="Shared across Pages 2–5 — edit here or on any other page.")
portfolio = st.session_state["portfolio"]

if not portfolio:
    st.warning("Add at least one firm to the portfolio to run the comparison.")
    st.stop()

rating_labels = st.session_state["rating_labels"]
loss_horizon = st.session_state["loss_horizon"]

transition_matrix_n = cached_transition_matrix_n(st.session_state["transition_matrix"], rating_labels, loss_horizon)
_, _, spot_rating = cached_spot_curves(st.session_state["rf_data"], st.session_state["credit_spread_data"], rating_labels)

try:
    kmv = cached_kmv(
        portfolio, loss_horizon, int(st.session_state["n_sim_kmv"]),
        float(st.session_state["confidence_kmv"]), int(st.session_state["kmv_seed"]),
    )
    credit_metrics = cached_credit_metrics(
        portfolio, transition_matrix_n, rating_labels, spot_rating, loss_horizon,
        float(st.session_state["confidence_creditmetrics"]),
        int(st.session_state["n_sim_creditmetrics"]), int(st.session_state["creditmetrics_seed"]),
    )
    maturity_override = None if st.session_state["basel_use_firm_maturity"] else float(st.session_state["basel_maturity_override"])
    basel = cached_basel(portfolio, transition_matrix_n, maturity_override)
except KeyError as exc:
    st.error(
        f"Every firm's rating must exist in the rating scale ({', '.join(rating_labels)}). "
        f"Missing: {exc}. Check the portfolio table or the Settings page."
    )
    st.stop()

st.info(
    f"Loss horizon = {loss_horizon:g}y · KMV: {st.session_state['n_sim_kmv']:,} sims @ "
    f"{st.session_state['confidence_kmv']:.1%} · CreditMetrics: {st.session_state['n_sim_creditmetrics']:,} sims @ "
    f"{st.session_state['confidence_creditmetrics']:.1%} · Basel: closed-form @ 99.9% (fixed). "
    "Adjust these on Pages 2–4."
)

comparison = pd.DataFrame({
    "Model": ["Merton–KMV", "CreditMetrics", "Basel Single-Factor"],
    "Type": ["Structural Monte Carlo", "Rating-migration Monte Carlo", "Closed-form (regulatory)"],
    "Confidence": [
        f"{st.session_state['confidence_kmv']:.1%}",
        f"{st.session_state['confidence_creditmetrics']:.1%}",
        "99.9% (fixed)",
    ],
    "Expected Loss": [kmv["expected_loss"], credit_metrics["expected_loss"], basel["expected_loss"]],
    "VaR / CVaR": [kmv["var"], credit_metrics["var"], basel["var"]],
    "Economic Capital": [kmv["economic_capital"], credit_metrics["economic_capital"], basel["economic_capital"]],
})

st.subheader("Headline comparison")
display_df = comparison.copy()
for col in ["Expected Loss", "VaR / CVaR", "Economic Capital"]:
    display_df[col] = display_df[col].map(lambda x: f"{x:,.2f}")
st.dataframe(display_df, width="stretch", hide_index=True)

st.subheader("Visual comparison")
fig = go.Figure()
fig.add_trace(go.Bar(name="Expected Loss", x=comparison["Model"], y=comparison["Expected Loss"], marker_color="#72B7B2"))
fig.add_trace(go.Bar(name="Economic Capital", x=comparison["Model"], y=comparison["Economic Capital"], marker_color="#F58518"))
fig.add_trace(go.Scatter(
    name="VaR / CVaR (total)", x=comparison["Model"], y=comparison["VaR / CVaR"],
    mode="markers", marker=dict(size=14, symbol="diamond", color="crimson"),
))
fig.update_layout(barmode="stack", height=440, yaxis_title="Amount", legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig, width="stretch")

with st.expander("Why don't the three models agree?"):
    st.markdown(
        """
They're not supposed to — each answers a slightly different question:

- **Merton–KMV** only ever sees two outcomes per firm (default / no
  default) and prices the *tail* directly through simulation — it's
  sensitive to `asset_mean`/`asset_std` and the correlation structure, but
  ignores credit spreads entirely.
- **CreditMetrics** prices *every* migration outcome, not just default, so
  a downgrade that doesn't trigger default still shows up as a loss (via
  revaluation on a wider spread). It's the only one of the three sensitive
  to the credit-spread curve.
- **Basel Single-Factor** is a regulatory formula calibrated to a
  particular asymptotic portfolio assumption (infinitely granular, single
  systematic factor) — it doesn't see *this specific* portfolio's
  correlation structure or spread curve at all, only each firm's own PD,
  LGD, EAD and maturity.

A small, concentrated, 3-firm demo portfolio is exactly the setting where
these differences show up most starkly — a large, diversified book tends
to bring the three closer together.
"""
    )
