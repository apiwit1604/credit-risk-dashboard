import streamlit as st

from credit_risk import merton, sample_data

st.set_page_config(page_title="Merton Structural Model", page_icon="🏢", layout="wide")
st.title("🏢 Merton Structural Model")
st.caption("Single-firm PD from equity value & volatility — equity is a call option on firm assets.")

with st.expander("How this model works", expanded=False):
    st.markdown(
        r"""
$$S = V\,N(d_1) - D e^{-rT} N(d_2), \qquad \sigma_E S = N(d_1)\,\sigma_V V$$

Two equations, two unknowns ($V$, $\sigma_V$) — solved by minimizing
squared pricing/volatility error. Default probability (risk-neutral):
$PD = N(-d_2)$. Full derivation: `docs/02_merton_structural.md`.
        """
    )

st.subheader("Inputs")
s = sample_data.MERTON_SAMPLE
c1, c2, c3 = st.columns(3)
S = c1.number_input("Equity Value (S)", value=float(s["S"]), format="%.2f")
D = c1.number_input("Face Value of Debt (D)", value=float(s["D"]), format="%.2f")
sigma_E = c2.number_input("Equity Volatility (σ_E)", value=float(s["sigma_E"]), format="%.6f")
r = c2.number_input("Risk-Free Rate (r)", value=float(s["r"]), format="%.4f")
T = c3.number_input("Horizon (T, years)", value=float(s["T"]), min_value=0.1, step=0.5)

if st.button("Calibrate Merton Model", type="primary"):
    result = merton.calibrate_merton(S=S, D=D, sigma_E=sigma_E, r=r, T=T)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Calibrated parameters**")
        st.dataframe(result.summary_table(), use_container_width=True, hide_index=True)
    with c2:
        st.metric("Risk-Neutral Probability of Default", f"{result.default_probability_rn * 100:.4f}%")
        st.metric("Implied Leverage (D / V)", f"{D / result.firm_value * 100:.1f}%")
        convergence = "✅ good" if result.sse < 1e-3 * max(S, 1) else "⚠️ check convergence (SSE looks high)"
        st.caption(f"Fit quality: {convergence}")
