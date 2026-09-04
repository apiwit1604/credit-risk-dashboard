import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from credit_risk import basel_single_factor, sample_data

st.set_page_config(page_title="Basel Single-Factor Capital", page_icon="🏦", layout="wide")
st.title("🏦 Basel Single-Factor Capital")
st.caption("Closed-form Basel IRB / ASRF regulatory capital — no simulation needed.")

with st.expander("How this model works", expanded=False):
    st.markdown(
        r"""
$$R(PD) = 0.12w + 0.24(1-w), \quad w = \frac{1-e^{-50PD}}{1-e^{-50}}$$

$$WCDR = \Phi\!\left[\frac{\Phi^{-1}(PD)}{\sqrt{1-R}} + \sqrt{\frac{R}{1-R}}\,\Phi^{-1}(0.999)\right],
\qquad K = LGD\cdot WCDR - LGD\cdot PD$$

Full derivation: `docs/05_basel_single_factor.md`.

⚠️ Assumes an **infinitely granular portfolio** (idiosyncratic risk fully
diversified) — for small/concentrated books like the samples in this
repo, that assumption doesn't hold; compare against the KMV or Credit VaR
pages, which don't make this assumption.

⚠️ `asset_correlation` here (computed as $R$ internally) uses the same
convention as the KMV page ($R=\rho^2$), not the Credit VaR — Ratings
Migration page. See `docs/06_correlation_conventions.md`.
        """
    )

st.subheader("Portfolio")
default_df = pd.DataFrame(sample_data.BASEL_PORTFOLIO).rename(columns={"name": "Firm", "ead": "EAD", "pd": "PD", "LGD": "LGD"})
portfolio_df = st.data_editor(default_df, num_rows="dynamic", use_container_width=True, key="basel_editor")

confidence = st.slider("Confidence level", min_value=0.95, max_value=0.999, value=0.999, step=0.001, format="%.3f")

if st.button("Compute Capital", type="primary"):
    portfolio = [
        {"name": row["Firm"], "ead": row["EAD"], "pd": row["PD"], "LGD": row["LGD"]}
        for _, row in portfolio_df.iterrows()
    ]
    df = basel_single_factor.run_portfolio_capital(portfolio, confidence=confidence)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Expected Loss", f"{df['Expected Loss'].sum():,.0f}")
    c2.metric("Total Capital Requirement", f"{df['Capital Requirement (K)'].sum():,.0f}")
    c3.metric("Total CVaR", f"{df['CVaR'].sum():,.0f}")

    st.dataframe(
        df.style.format({
            "EAD": "{:,.0f}", "PD": "{:.2%}", "LGD": "{:.1%}", "Correlation (R)": "{:.3f}",
            "Expected Loss": "{:,.0f}", "Capital Requirement (K)": "{:,.0f}", "CVaR": "{:,.0f}",
        }),
        use_container_width=True, hide_index=True,
    )

    fig = go.Figure(go.Bar(x=df["Firm"], y=df["Capital Requirement (K)"], name="Capital Requirement"))
    fig.add_trace(go.Bar(x=df["Firm"], y=df["Expected Loss"], name="Expected Loss"))
    fig.update_layout(barmode="group", title="Capital vs. Expected Loss by firm", yaxis_title="Amount", height=420)
    st.plotly_chart(fig, use_container_width=True)
