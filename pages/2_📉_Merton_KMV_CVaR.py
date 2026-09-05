# -*- coding: utf-8 -*-
"""Page 2 — Merton-KMV structural (asset-value) Monte Carlo Credit VaR."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.compute import cached_kmv
from src.state import init_state
from src.ui_components import render_portfolio_editor

st.set_page_config(page_title="Merton–KMV Credit VaR", page_icon="📉", layout="wide")
init_state()

st.title("Merton–KMV Structural Credit VaR")

with st.expander("Methodology", expanded=False):
    st.markdown(
        r"""
Each firm's assets are simulated one year (or `loss_horizon`) forward under
a **single-factor Gaussian copula**:

$$
Z_i = \sqrt{\rho_i}\, M + \sqrt{1-\rho_i}\, \varepsilon_i, \qquad M, \varepsilon_i \sim \mathcal{N}(0,1) \text{ i.i.d.}
$$

$$
V_{i,T} = V_{i,0}\, \exp\!\big(T\,(\mu_i + \sigma_i Z_i)\big)
$$

where $M$ is a common systematic shock shared by every firm and $\rho_i$
(`asset_correlation`) is firm $i$'s loading on it — this is what makes
defaults correlated across the portfolio instead of independent coin
flips. A firm **defaults** in a given simulation draw if its simulated
asset value falls below its EAD (a simplified default barrier standing in
for the firm's debt value):

$$
\text{Default}_i \iff V_{i,T} < \text{EAD}_i, \qquad \text{Loss}_i = \text{EAD}_i \times \text{LGD}_i \times \mathbb{1}_{\text{Default}_i}
$$

Portfolio loss is the sum across firms, simulated `n_sims` times. **VaR**
is the empirical quantile of that loss distribution at the chosen
confidence level; **Expected Shortfall** is the average loss *beyond* VaR;
**Economic Capital** is VaR net of the expected loss already priced in.
        """
    )

st.subheader("Portfolio")
render_portfolio_editor(key="portfolio_editor_kmv", caption="Shared across Pages 2–5 — edit here or on any other page.")
portfolio = st.session_state["portfolio"]

st.subheader("Simulation settings")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.session_state["loss_horizon"] = st.number_input(
        "Loss horizon (years)", min_value=0.08, max_value=5.0,
        value=float(st.session_state["loss_horizon"]), step=0.25,
        help="Shared with Pages 3 and 4.",
    )
with c2:
    st.session_state["n_sim_kmv"] = st.select_slider(
        "Number of simulations",
        options=[10_000, 50_000, 100_000, 200_000, 500_000, 1_000_000],
        value=st.session_state["n_sim_kmv"],
    )
with c3:
    st.session_state["confidence_kmv"] = st.select_slider(
        "Confidence level", options=[0.95, 0.99, 0.995, 0.999],
        value=st.session_state["confidence_kmv"],
    )
with c4:
    st.session_state["kmv_seed"] = st.number_input(
        "Random seed", min_value=0, value=int(st.session_state["kmv_seed"]), step=1,
        help="Fixed so results are reproducible; change it to sanity-check simulation noise.",
    )

if not portfolio:
    st.warning("Add at least one firm to the portfolio to run the simulation.")
    st.stop()

results = cached_kmv(
    portfolio, st.session_state["loss_horizon"], int(st.session_state["n_sim_kmv"]),
    float(st.session_state["confidence_kmv"]), int(st.session_state["kmv_seed"]),
)

st.subheader("Results")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Expected Loss", f"{results['expected_loss']:,.2f}")
m2.metric(f"VaR ({st.session_state['confidence_kmv']:.1%})", f"{results['var']:,.2f}")
m3.metric("Expected Shortfall", f"{results['expected_shortfall']:,.2f}")
m4.metric("Economic Capital", f"{results['economic_capital']:,.2f}")

left, right = st.columns([2, 1])
with left:
    st.markdown("**Portfolio loss distribution**")
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=results["total_loss"], nbinsx=60, name="Simulated loss", marker_color="#4C78A8"))
    fig.add_vline(x=results["var"], line_dash="dash", line_color="crimson",
                  annotation_text="VaR", annotation_position="top right")
    fig.add_vline(x=results["expected_loss"], line_dash="dot", line_color="gray",
                  annotation_text="Expected Loss", annotation_position="top left")
    fig.update_layout(height=420, xaxis_title="Portfolio loss", yaxis_title="Simulated draws", showlegend=False)
    st.plotly_chart(fig, width="stretch")
with right:
    st.markdown("**Simulated PD by firm**")
    pd_df = results["pd"].copy()
    pd_df["Probability of Default (PD)"] = pd_df["Probability of Default (PD)"].map(lambda x: f"{x:.2%}")
    st.dataframe(pd_df, width="stretch", hide_index=True)

st.markdown("**Joint default/solvency scenarios**")
st.caption("Column order matches the portfolio table above (Firm 1, Firm 2, …). 'D' = default, 'S' = solvent.")
event_df = results["event_summary"].sort_values("PB", ascending=False).reset_index(drop=True)
event_df["PB"] = event_df["PB"].map(lambda x: f"{x:.4%}")
st.dataframe(event_df, width="stretch", hide_index=True)
