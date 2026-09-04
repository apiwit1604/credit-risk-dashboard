import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from credit_risk import bond_pd, sample_data

st.set_page_config(page_title="Bond-Implied PD — Credit Spread", page_icon="📉", layout="wide")
st.title("📉 Bond-Implied PD — Credit Spread")
st.caption("PD bootstrapped from the ratio of a risky vs. riskless bond price at each maturity.")

with st.expander("How this model works", expanded=False):
    st.markdown(
        r"""
Under risk-neutral pricing with zero recovery, a risky bond's price is the
riskless price scaled by the survival probability:

$$
Q(\tau>t) = \frac{P^{risky}_t}{P^{rf}_t}
$$

Full derivation: `docs/01_bond_implied_pd.md`.
        """
    )

st.subheader("Inputs")
default_n = len(sample_data.BOND_SPREAD_SAMPLE["risk_free_rates"])
n_periods = st.number_input("Number of periods", min_value=1, max_value=15, value=default_n, step=1)

default_df = pd.DataFrame({
    "Period": np.arange(1, default_n + 1),
    "Risk-Free Rate": sample_data.BOND_SPREAD_SAMPLE["risk_free_rates"],
    "Risky Rate": sample_data.BOND_SPREAD_SAMPLE["risky_rates"],
})
if n_periods != default_n:
    default_df = pd.DataFrame({
        "Period": np.arange(1, n_periods + 1),
        "Risk-Free Rate": np.interp(np.linspace(0, 1, n_periods), np.linspace(0, 1, default_n), default_df["Risk-Free Rate"]),
        "Risky Rate": np.interp(np.linspace(0, 1, n_periods), np.linspace(0, 1, default_n), default_df["Risky Rate"]),
    })

edited = st.data_editor(default_df, num_rows="fixed", use_container_width=True, key="spread_curve_editor")
face_value = st.number_input("Face value", value=100.0, step=10.0)

if st.button("Run", type="primary", key="run_spread"):
    result = bond_pd.bootstrap_pd_from_spread(
        risk_free_rates=edited["Risk-Free Rate"].to_numpy(),
        risky_rates=edited["Risky Rate"].to_numpy(),
        face_value=face_value,
    )

    st.subheader("Results")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Bond prices & credit spread**")
        st.dataframe(result.prices_table(), use_container_width=True, hide_index=True)
    with c2:
        st.markdown("**Default probabilities**")
        st.dataframe(result.pd_table(), use_container_width=True, hide_index=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=result.period, y=result.unconditional_pd * 100, name="Unconditional PD (%)"))
    fig.add_trace(go.Scatter(x=result.period, y=result.cum_default_prob * 100, name="Cumulative Default Prob (%)", mode="lines+markers"))
    fig.update_layout(xaxis_title="Period", yaxis_title="%", title="PD term structure", height=420)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Edit the curve above (or leave the sample data) and click **Run**.")
