# -*- coding: utf-8 -*-
"""Page 5 — Side-by-side comparison of the three Credit VaR models.

Unlike Pages 2-4, this page's simulation settings (loss horizon, number of
simulations, confidence level, random seed, flat Basel maturity) are their
own, independent `compare_*` session-state keys — not read from Pages 2-4.
That's deliberate: this page is meant to give one clean, self-contained
snapshot for comparing the three models under one shared set of
assumptions, without silently depending on whatever the user last set on
another page.
"""
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
from src.ui_components import render_full_portfolio_editor

st.set_page_config(page_title="Credit VaR Model Comparison", layout="wide")
init_state()

st.title("Credit VaR Model Comparison")
st.caption(
    "Runs the same portfolio through Merton–KMV, CreditMetrics, and Basel Single-Factor, "
    "using the settings below — set independently of Pages 2–4, so this page always reflects "
    "exactly what's configured here."
)

st.subheader("Portfolio (every field)")
render_full_portfolio_editor(
    key="portfolio_editor_compare",
    caption="Full firm record — this is the only page that shows every field at once, so it's also the "
            "right place to rename a firm without resetting fields hidden on the other pages.",
)
portfolio = st.session_state["portfolio"]

st.subheader("Comparison settings")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.session_state["compare_loss_horizon"] = st.number_input(
        "Loss horizon (years)", min_value=0.08, max_value=5.0,
        value=float(st.session_state["compare_loss_horizon"]), step=0.25,
    )
with c2:
    st.session_state["compare_n_sims"] = st.select_slider(
        "Number of simulations",
        options=[10_000, 50_000, 100_000, 200_000, 500_000, 1_000_000],
        value=st.session_state["compare_n_sims"],
        help="Used for both Merton–KMV and CreditMetrics on this page.",
    )
with c3:
    st.session_state["compare_confidence"] = st.select_slider(
        "Confidence level", options=[0.95, 0.99, 0.995, 0.999],
        value=st.session_state["compare_confidence"],
        help="Used for both Merton–KMV and CreditMetrics. Basel is always fixed at 99.9% by regulation.",
    )
with c4:
    st.session_state["compare_seed"] = st.number_input(
        "Random seed", min_value=0, value=int(st.session_state["compare_seed"]), step=1,
        help="Used for both Monte Carlo models, so the comparison isn't confounded by independent simulation noise.",
    )
with c5:
    st.session_state["compare_maturity"] = st.number_input(
        "Flat maturity M for every firm (years)", min_value=1.0, max_value=5.0,
        value=float(st.session_state["compare_maturity"]), step=0.5,
        help="Basel's effective maturity input on this page — applied uniformly, independent of Page 4's toggle.",
    )

if not portfolio:
    st.warning("Add at least one firm to the portfolio to run the comparison.")
    st.stop()

rating_labels = st.session_state["rating_labels"]
loss_horizon = st.session_state["compare_loss_horizon"]
n_sims = int(st.session_state["compare_n_sims"])
confidence = float(st.session_state["compare_confidence"])
seed = int(st.session_state["compare_seed"])
maturity = float(st.session_state["compare_maturity"])

transition_matrix_n = cached_transition_matrix_n(st.session_state["transition_matrix"], rating_labels, loss_horizon)
_, _, spot_rating = cached_spot_curves(st.session_state["rf_data"], st.session_state["credit_spread_data"], rating_labels)

try:
    kmv = cached_kmv(portfolio, loss_horizon, n_sims, confidence, seed)
    credit_metrics = cached_credit_metrics(
        portfolio, transition_matrix_n, rating_labels, spot_rating, loss_horizon, confidence, n_sims, seed,
    )
    basel = cached_basel(portfolio, transition_matrix_n, maturity, confidence)
except KeyError as exc:
    st.error(
        f"Every firm's rating must exist in the rating scale ({', '.join(rating_labels)}). "
        f"Missing: {exc}. Check the portfolio table or the Settings page."
    )
    st.stop()

st.info(
    f"Loss horizon = {loss_horizon:g}y · {n_sims:,} simulations @ {confidence:.1%} for KMV & CreditMetrics & Basel"
    f"Basel: closed-form with flat M = {maturity:g}y."
)

comparison = pd.DataFrame({
    "Model": ["Merton–KMV", "CreditMetrics", "Basel Single-Factor"],
    "Type": ["Structural Monte Carlo", "Rating-migration Monte Carlo", "Closed-form (regulatory)"],
    "Confidence": [f"{confidence:.1%}", f"{confidence:.1%}", "99.9% (fixed)"],
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
  LGD, EAD and the flat maturity set above.

A small, concentrated, 3-firm demo portfolio is exactly the setting where
these differences show up most starkly — a large, diversified book tends
to bring the three closer together.
"""
    )
