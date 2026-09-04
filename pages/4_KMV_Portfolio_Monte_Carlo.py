import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from credit_risk import kmv_montecarlo, sample_data

st.set_page_config(page_title="KMV Portfolio Monte Carlo", page_icon="🎲", layout="wide")
st.title("🎲 KMV Portfolio Monte Carlo")
st.caption("Merton model simulated across a correlated portfolio — Expected Loss, VaR, CVaR, Economic Capital.")

with st.expander("How this model works", expanded=False):
    st.markdown(
        r"""
$$Z_i = \sqrt{R_i}\,M + \sqrt{1-R_i}\,\varepsilon_i, \qquad
V_{i,T} = V_{i,0}\exp\!\big[(\mu_i-\tfrac12\sigma_i^2)T + \sigma_i\sqrt T Z_i\big]$$

Default when $V_{i,T} < D_i$. Full derivation: `docs/03_kmv_montecarlo.md`.

⚠️ **`asset_correlation` here is $R = \rho^2$** (Basel-R convention) —
different from the Credit VaR — Ratings Migration page. See
`docs/06_correlation_conventions.md`.
        """
    )

st.subheader("Portfolio")
default_df = pd.DataFrame(sample_data.KMV_PORTFOLIO).rename(columns={
    "name": "Name", "asset": "Asset (V0)", "debt": "Debt (D)", "mean": "Mean Return (μ)",
    "standard_deviation": "Asset Vol (σ)", "lgd": "LGD", "asset_correlation": "Asset Correlation (R)",
})
portfolio_df = st.data_editor(default_df, num_rows="dynamic", use_container_width=True, key="kmv_editor")

c1, c2, c3 = st.columns(3)
n_sims = c1.select_slider("Number of simulations", options=[10_000, 50_000, 100_000, 250_000, 500_000], value=100_000)
confidence = c2.slider("Confidence level", min_value=0.90, max_value=0.999, value=0.999, step=0.001, format="%.3f")
seed = c3.number_input("Random seed", value=42, step=1)

if st.button("Run Simulation", type="primary"):
    portfolio = [
        {
            "name": row["Name"], "asset": row["Asset (V0)"], "debt": row["Debt (D)"],
            "mean": row["Mean Return (μ)"], "standard_deviation": row["Asset Vol (σ)"],
            "lgd": row["LGD"], "asset_correlation": row["Asset Correlation (R)"],
        }
        for _, row in portfolio_df.iterrows()
    ]

    with st.spinner(f"Running {n_sims:,} Monte Carlo paths..."):
        result = kmv_montecarlo.run_kmv_portfolio_simulation(portfolio, n_sims=n_sims, confidence_level=confidence, random_seed=int(seed))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Expected Loss", f"{result.expected_loss:,.0f}")
    c2.metric(f"VaR ({confidence:.1%})", f"{result.var:,.0f}")
    c3.metric(f"CVaR ({confidence:.1%})", f"{result.cvar:,.0f}")
    c4.metric("Economic Capital", f"{result.economic_capital:,.0f}")

    fig = go.Figure(go.Histogram(x=result.total_loss, nbinsx=60))
    fig.add_vline(x=result.var, line_dash="dash", line_color="orange", annotation_text="VaR")
    fig.add_vline(x=result.expected_loss, line_dash="dot", line_color="green", annotation_text="EL")
    fig.update_layout(title="Simulated portfolio loss distribution", xaxis_title="Portfolio Loss", yaxis_title="Frequency", height=420)
    st.plotly_chart(fig, use_container_width=True)

    default_freq = pd.DataFrame({
        "Firm": [p["name"] for p in portfolio],
        "Simulated Default Rate": result.default_matrix.mean(axis=1),
    })
    st.markdown("**Per-firm simulated default frequency**")
    st.dataframe(default_freq.style.format({"Simulated Default Rate": "{:.3%}"}), use_container_width=True, hide_index=True)
