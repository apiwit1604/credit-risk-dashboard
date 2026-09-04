import numpy as np
import plotly.graph_objects as go
import streamlit as st

from credit_risk import bond_calibration, sample_data

st.set_page_config(page_title="Bond-Implied PD — Price Calibration", page_icon="💵", layout="wide")
st.title("💵 Bond-Implied PD — Price Calibration")
st.caption("Solve for the PD (flat, or a full term structure) that reprices an observed market bond.")

with st.expander("How this model works", expanded=False):
    st.markdown(
        r"""
Price a defaultable bond as the risk-neutral expected value of its cash
flows under a candidate PD, then solve for the PD that matches the
observed market price. Full derivation: `docs/01_bond_implied_pd.md`.

**Identification warning:** the term-structure variant fits one PD per
period against a *single* price constraint — the fit is under-determined.
        """
    )

tab_flat, tab_term = st.tabs(["Flat PD", "Term-Structure PD"])

with tab_flat:
    s = sample_data.BOND_CALIBRATION_SAMPLE["flat"]
    c1, c2, c3 = st.columns(3)
    market_price = c1.number_input("Market Price", value=float(s["market_price"]), key="flat_mp")
    face_value = c1.number_input("Face Value", value=float(s["face_value"]), key="flat_fv")
    coupon = c2.number_input("Coupon per Period", value=float(s["coupon"]), key="flat_c")
    recovery = c2.number_input("Recovery Value", value=float(s["recovery"]), key="flat_r")
    rf_text = c3.text_input("Risk-Free Rates (comma-separated)", value=",".join(str(x) for x in s["risk_free_rates"]), key="flat_rf")

    if st.button("Calibrate", type="primary", key="run_flat"):
        rf = [float(x) for x in rf_text.split(",")]
        result = bond_calibration.calibrate_flat_pd(market_price, face_value, coupon, recovery, rf)

        st.success(f"Calibrated PD: **{result.pd[0] * 100:.4f}%**  (SSE = {result.sse:.2e}, model price = {result.model_price:.4f})")
        st.dataframe(result.cashflow_table(), use_container_width=True, hide_index=True)

with tab_term:
    s = sample_data.BOND_CALIBRATION_SAMPLE["term"]
    c1, c2, c3 = st.columns(3)
    market_price = c1.number_input("Market Price", value=float(s["market_price"]), key="term_mp")
    face_value = c1.number_input("Face Value", value=float(s["face_value"]), key="term_fv")
    coupon = c2.number_input("Coupon per Period", value=float(s["coupon"]), key="term_c")
    recovery = c2.number_input("Recovery Value", value=float(s["recovery"]), key="term_r")
    rf_text = c3.text_input("Risk-Free Rates (comma-separated)", value=",".join(str(x) for x in s["risk_free_rates"]), key="term_rf")

    if st.button("Calibrate", type="primary", key="run_term"):
        rf = [float(x) for x in rf_text.split(",")]
        result = bond_calibration.calibrate_term_structure_pd(market_price, face_value, coupon, recovery, rf)

        st.success(f"SSE = {result.sse:.2e}, model price = {result.model_price:.4f}")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**PD term structure**")
            st.dataframe(result.pd_table(), use_container_width=True, hide_index=True)
        with c2:
            fig = go.Figure(go.Bar(x=result.period, y=np.asarray(result.pd) * 100))
            fig.update_layout(xaxis_title="Period", yaxis_title="PD (%)", title="Calibrated PD by period", height=350)
            st.plotly_chart(fig, use_container_width=True)
        st.caption("⚠️ Remember: this term structure is one of many that fit the single price constraint — see the identification warning above.")
