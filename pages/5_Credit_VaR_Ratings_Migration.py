import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from credit_risk import credit_var_ratings, sample_data

st.set_page_config(page_title="Credit VaR — Ratings Migration", page_icon="📊", layout="wide")
st.title("📊 Credit VaR — Ratings Migration")
st.caption("CreditMetrics-style: simulates full rating migrations (not just default) and revalues on the new curve.")

with st.expander("How this model works", expanded=False):
    st.markdown(
        r"""
$$Z_i = \rho_i M + \sqrt{1-\rho_i^2}\,\varepsilon_i$$

Map $Z_i$ to a migrated rating via inverse-normal thresholds built from
the transition matrix, then revalue each position on its new rating's
credit curve. Full derivation: `docs/04_credit_var_ratings.md`.

⚠️ **`asset_correlation` here is $\rho$ directly** — different from the
KMV / Basel pages, which use $R=\rho^2$. See
`docs/06_correlation_conventions.md`.

⚠️ **Multi-year positions** (`years_to_maturity` > 1) reuse the 1-year
transition matrix as an approximation — see `docs/04_credit_var_ratings.md`.
        """
    )

st.subheader("Portfolio")
default_portfolio_df = pd.DataFrame(sample_data.CREDIT_VAR_PORTFOLIO).rename(columns={
    "name": "Name", "rating": "Rating", "years_to_maturity": "Years to Maturity",
    "asset_correlation": "Asset Correlation (ρ)", "ead": "EAD", "coupon_rate": "Coupon Rate",
    "payments_per_year": "Payments / Year", "LGD": "LGD",
})
portfolio_df = st.data_editor(default_portfolio_df, num_rows="dynamic", use_container_width=True, key="cvr_editor")

with st.expander("Transition matrix & credit curve (advanced — defaults to ThaiBMA sample data)"):
    st.caption("1-year ratings transition matrix. Each row must sum to 1.0.")
    tm_df = pd.DataFrame(sample_data.TRANSITION_MATRIX, columns=sample_data.RATING_LABELS, index=sample_data.RATING_LABELS)
    tm_edited = st.data_editor(tm_df, use_container_width=True, key="tm_editor")

    row_sums = tm_edited.sum(axis=1)
    bad_rows = row_sums[abs(row_sums - 1.0) > 1e-6]
    if len(bad_rows):
        st.error(f"These rows don't sum to 1.0 and will break the model: {list(bad_rows.index)}")

n_sims = st.select_slider("Number of simulations", options=[10_000, 50_000, 100_000, 250_000], value=50_000)
alpha = st.slider("Confidence level (α)", min_value=0.90, max_value=0.999, value=0.999, step=0.001, format="%.3f")
seed = st.number_input("Random seed", value=1, step=1)

if st.button("Run Simulation", type="primary"):
    portfolio = [
        {
            "name": row["Name"], "rating": row["Rating"], "years_to_maturity": int(row["Years to Maturity"]),
            "asset_correlation": row["Asset Correlation (ρ)"], "ead": row["EAD"],
            "coupon_rate": row["Coupon Rate"], "payments_per_year": int(row["Payments / Year"]), "LGD": row["LGD"],
        }
        for _, row in portfolio_df.iterrows()
    ]
    spot_curve = sample_data.build_spot_curve_by_rating()

    with st.spinner(f"Running {n_sims:,} Monte Carlo paths..."):
        result = credit_var_ratings.run_credit_var_ratings(
            portfolio, tm_edited.to_numpy(), list(tm_edited.columns), spot_curve,
            n_sims=n_sims, alpha=alpha, random_seed=int(seed),
        )

    c1, c2, c3 = st.columns(3)
    c1.metric("Expected Loss", f"{result.expected_loss:,.0f}")
    c2.metric(f"Credit VaR ({alpha:.1%})", f"{result.credit_var:,.0f}")
    c3.metric("Expected Shortfall", f"{result.expected_shortfall:,.0f}")
    st.metric("Economic Capital", f"{result.economic_capital:,.0f}")

    fig = go.Figure(go.Bar(
        x=result.detail_table["Scenario"], y=result.detail_table["Loss"],
        marker_color=result.detail_table["Probability"], marker_colorscale="Reds",
        hovertext=[f"P={p:.4%}" for p in result.detail_table["Probability"]],
    ))
    fig.update_layout(title="Loss by joint rating scenario (color = probability)", xaxis_title="Scenario", yaxis_title="Loss", height=420)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Full scenario detail**")
    st.dataframe(
        result.detail_table.style.format({"Probability": "{:.4%}", "Loss": "{:,.2f}", "Cumulative Probability": "{:.4%}"}),
        use_container_width=True, hide_index=True,
    )
