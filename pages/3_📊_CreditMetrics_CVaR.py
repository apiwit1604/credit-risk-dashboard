# -*- coding: utf-8 -*-
"""Page 3 — CreditMetrics rating-migration Monte Carlo Credit VaR."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.compute import cached_credit_metrics, cached_spot_curves, cached_transition_matrix_n
from src.state import init_state
from src.ui_components import render_model_portfolio_editor

st.set_page_config(page_title="CreditMetrics Credit VaR", page_icon="📊", layout="wide")
init_state()

st.title("📊 CreditMetrics Rating-Migration Credit VaR")

with st.expander("📖 Methodology", expanded=False):
    st.markdown(
        r"""
Instead of asking "did the firm default?", CreditMetrics asks **"what
rating did the firm migrate to?"** and revalues the exposure under every
possible outcome.

**1. Migration probabilities.** The 1-year transition matrix $P$ (Settings
page) is raised to a fractional power to match `loss_horizon` $h$:
$P_h = P^{h}$. Cumulative migration probabilities are turned into
threshold $z$-scores via the inverse normal CDF:
$z_k = \Phi^{-1}\!\left(\sum_{j \le k} P_h(\text{rating}, j)\right)$.

**2. Correlated migration draws.** As in the KMV model, each firm's latent
variable uses a single-factor Gaussian copula,
$Z_i = \rho_i M + \sqrt{1-\rho_i^2}\,\varepsilon_i$, and its simulated
ending rating is whichever threshold bucket $Z_i$ falls into.

**3. Revaluation.** For every possible ending rating, the exposure is
repriced by discounting its remaining cash flows on that rating's
forward curve (built from the risk-free curve + credit spread curve on
the Settings page):
$$
V(\text{rating}) = \sum_t \frac{CF_t}{(1+f_t(\text{rating}))^{t-h}}
$$
Loss for a firm in a given draw = (value under its **current** rating) −
(value under its **simulated** rating). Portfolio loss sums across firms;
**VaR**, **Expected Shortfall** and **Economic Capital** are computed the
same way as on the KMV page.
        """
    )

st.subheader("Portfolio")
render_model_portfolio_editor(
    "creditmetrics", key="portfolio_editor_cm",
    caption="Only the fields CreditMetrics reads: Firm, Rating, Asset Corr., Maturity (yrs), EAD, Coupon Rate, "
            "Payments/Yr, LGD. Asset value/drift/vol are edited on the Merton–KMV or Model Comparison page.",
)
portfolio = st.session_state["portfolio"]

st.subheader("Simulation settings")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.session_state["loss_horizon"] = st.number_input(
        "Loss horizon (years)", min_value=0.08, max_value=5.0,
        value=float(st.session_state["loss_horizon"]), step=0.25,
        help="Shared with Pages 2 and 4.", key="horizon_cm",
    )
with c2:
    st.session_state["n_sim_creditmetrics"] = st.select_slider(
        "Number of simulations",
        options=[10_000, 50_000, 100_000, 200_000, 500_000, 1_000_000],
        value=st.session_state["n_sim_creditmetrics"],
    )
with c3:
    st.session_state["confidence_creditmetrics"] = st.select_slider(
        "Confidence level", options=[0.95, 0.99, 0.995, 0.999],
        value=st.session_state["confidence_creditmetrics"],
    )
with c4:
    st.session_state["creditmetrics_seed"] = st.number_input(
        "Random seed", min_value=0, value=int(st.session_state["creditmetrics_seed"]), step=1,
    )

if not portfolio:
    st.warning("Add at least one firm to the portfolio to run the simulation.")
    st.stop()

rating_labels = st.session_state["rating_labels"]
transition_matrix_n = cached_transition_matrix_n(
    st.session_state["transition_matrix"], rating_labels, st.session_state["loss_horizon"]
)
_, _, spot_rating = cached_spot_curves(
    st.session_state["rf_data"], st.session_state["credit_spread_data"], rating_labels
)

try:
    results = cached_credit_metrics(
        portfolio, transition_matrix_n, rating_labels, spot_rating,
        st.session_state["loss_horizon"], float(st.session_state["confidence_creditmetrics"]),
        int(st.session_state["n_sim_creditmetrics"]), int(st.session_state["creditmetrics_seed"]),
    )
except KeyError as exc:
    st.error(
        f"Every firm's rating must exist in the rating scale ({', '.join(rating_labels)}). "
        f"Missing: {exc}. Check the portfolio table or the Settings page."
    )
    st.stop()

st.subheader("Results")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Expected Loss", f"{results['expected_loss']:,.2f}")
m2.metric(f"VaR ({st.session_state['confidence_creditmetrics']:.1%})", f"{results['var']:,.2f}")
m3.metric("Expected Shortfall", f"{results['expected_shortfall']:,.2f}")
m4.metric("Economic Capital", f"{results['economic_capital']:,.2f}")

left, right = st.columns([2, 1])
with left:
    st.markdown("**Portfolio loss distribution**")
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=results["total_losses"], nbinsx=60, name="Simulated loss", marker_color="#E45756"))
    fig.add_vline(x=results["var"], line_dash="dash", line_color="crimson",
                  annotation_text="VaR", annotation_position="top right")
    fig.add_vline(x=results["expected_loss"], line_dash="dot", line_color="gray",
                  annotation_text="Expected Loss", annotation_position="top left")
    fig.update_layout(height=420, xaxis_title="Portfolio loss", yaxis_title="Simulated draws", showlegend=False)
    st.plotly_chart(fig, width="stretch")
with right:
    st.markdown("**Multi-year transition matrix**")
    st.caption(f"P^{st.session_state['loss_horizon']:g} — row = starting rating")
    st.dataframe(transition_matrix_n.style.format("{:.2%}"), width="stretch")

st.markdown("**Top loss scenarios**")
st.caption(
    "Highest-loss joint migration outcomes across the simulated draws. "
    "Scenario order matches the portfolio table (Firm 1, Firm 2, …)."
)
top_events = results["event_summary"].head(15).copy()
top_events["Probability"] = top_events["Probability"].map(lambda x: f"{x:.4%}")
top_events["Loss_Amount"] = top_events["Loss_Amount"].map(lambda x: f"{x:,.2f}")
st.dataframe(top_events, width="stretch", hide_index=True)
