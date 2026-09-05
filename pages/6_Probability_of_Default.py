# -*- coding: utf-8 -*-
"""Page 6 — Probability of Default: four independent estimation methods."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.default_probability.credit_spread_bootstrap import analyze_credit_risk
from src.default_probability.jarrow_turnbull import run_jarrow_turnbull_many_pd, run_jarrow_turnbull_one_pd
from src.default_probability.merton_structural import merton_model
from src.state import init_state

st.set_page_config(page_title="Probability of Default", page_icon="🎯", layout="wide")
init_state()

st.title("Probability of Default — Four Methods")
st.caption(
    "Unlike Pages 2–5, these methods work off a single firm/bond at a time, not the shared portfolio — "
    "they're independent PD-estimation techniques, not part of the Credit VaR pipeline."
)

tab_merton, tab_jt1, tab_jtn, tab_spread = st.tabs([
    "Merton (structural)", "Jarrow–Turnbull (flat PD)",
    "Jarrow–Turnbull (term structure)", "Credit-spread bootstrap",
])

# ---------------------------------------------------------------------------
# Tab 1 — Merton structural model
# ---------------------------------------------------------------------------
with tab_merton:
    with st.expander("Methodology", expanded=False):
        st.markdown(
            r"""
Equity is treated as a European call option on the firm's assets. Given
the market value of equity $S$, the volatility of equity $\sigma$, the
face value of debt $D$ and the risk-free rate $r$, the model solves
*jointly* for the unobservable asset value $V$ and asset volatility
$\sigma_V$ so that both the Black–Scholes option-pricing equation and the
$\sigma \leftrightarrow \sigma_V$ relationship (via Itô's lemma) hold:
$$
S = V\,\Phi(d_1) - D e^{-rT}\Phi(d_2), \qquad \sigma S = \Phi(d_1)\,\sigma_V\,V
$$
$$
d_1 = \frac{\ln(V/D) + (r + \tfrac{1}{2}\sigma_V^2)T}{\sigma_V\sqrt{T}}, \qquad d_2 = d_1 - \sigma_V\sqrt{T}
$$
The **risk-neutral PD** is then $1-\Phi(d_2)$ — "risk-neutral" because it
uses $r$ as the asset drift, per Black–Scholes valuation, *not* the firm's
real-world expected return. This is deliberately not the same thing as a
real-world ("physical") default probability, which would need the firm's
actual expected asset return and typically an empirical mapping (as in
Moody's KMV EDF) rather than a pure option-pricing argument.
"""
        )
        st.caption(
            "Known simplification: solved here via a single penalized least-squares "
            "objective (Nelder–Mead), rather than the exact 2-equation solve "
            "(e.g. `scipy.optimize.fsolve`) — a documented, not-yet-changed limitation."
        )

    c1, c2 = st.columns(2)
    with c1:
        s_val = st.number_input("Market value of equity (S)", min_value=0.01, value=1000.0, step=50.0)
        d_val = st.number_input("Face value of debt (D)", min_value=0.01, value=2000.0, step=50.0)
    with c2:
        sigma_val = st.number_input("Equity volatility (σ, annualised)", min_value=0.001, value=0.75, step=0.05, format="%.4f")
        r_val = st.number_input("Risk-free rate (r, annualised)", value=0.12, step=0.005, format="%.4f")
    t_val = st.number_input("Time to debt maturity (T, years)", min_value=0.01, value=1.0, step=0.25)

    summary, pd_result = merton_model(equity_value=s_val, debt_face_value=d_val, equity_vol=sigma_val, risk_free_rate=r_val, maturity=t_val)

    m1, m2, m3 = st.columns(3)
    m1.metric("Optimal Firm Value (V)", f"{summary.loc['Optimal Firm Value', 'Value']:,.2f}")
    m2.metric("Optimal Asset Vol (σ_V)", f"{summary.loc['Optimal Asset Vol (sigma_V)', 'Value']:.2%}")
    m3.metric("Risk-Neutral PD", f"{pd_result.loc['Risk-Neutral PD', 'Value']:.2%}")
    st.caption(f"Fit quality (SSE, lower is better): {summary.loc['SSE', 'Value']:.6f}")

# ---------------------------------------------------------------------------
# Tab 2 & 3 — Jarrow-Turnbull
# ---------------------------------------------------------------------------
def _rf_curve_editor(key_prefix: str) -> list[tuple[float, float]]:
    st.caption("Defaults to the risk-free curve from the Settings page — edit freely, it won't change Settings.")
    df = pd.DataFrame(st.session_state["rf_data"], columns=["Tenor (yrs)", "Risk-free rate"])
    edited = st.data_editor(df, key=f"{key_prefix}_rf_curve", num_rows="dynamic", width="stretch", hide_index=True)
    return list(edited.itertuples(index=False, name=None))


with tab_jt1:
    with st.expander("Methodology", expanded=False):
        st.markdown(
            r"""
Default is modeled as a constant risk-neutral hazard rate $PD$ per period.
Cumulative survival to the start of period $t$ is $(1-PD)^{t-1}$, so the
probability of defaulting *exactly* in period $t$ (for the first time) is
$(1-PD)^{t-1}\,PD$ — the model's single free parameter $PD$ is calibrated
by minimizing the squared difference between the model's theoretical bond
price and the observed market price:
$$
\text{Price} = \sum_t \Big[(1-PD)^{t-1}PD \cdot \text{Recovery} + (1-PD)^t \cdot CF_t\Big]\big/(1+r_f(t))^{t}
$$
Cash flows are discounted on the **risk-free** curve — default risk is
already priced in through the survival/default weighting, not through a
credit spread.
"""
        )
    c1, c2, c3 = st.columns(3)
    with c1:
        market_price_1 = st.number_input("Observed market price", min_value=0.01, value=90.0, step=1.0, key="mp1")
        face_value_1 = st.number_input("Face value", min_value=0.01, value=100.0, step=10.0, key="fv1")
    with c2:
        coupon_rate_1 = st.number_input("Coupon rate (annual)", min_value=0.0, value=0.04, step=0.005, format="%.4f", key="cr1")
        freq_1 = st.number_input("Payments per year", min_value=0, value=4, step=1, key="freq1")
    with c3:
        bond_years_1 = st.number_input("Years to maturity", min_value=0.25, value=2.0, step=0.25, key="by1")
        recovery_1 = st.number_input("Recovery rate", min_value=0.0, max_value=1.0, value=0.40, step=0.05, key="rec1")

    with st.expander("Risk-free curve used for discounting"):
        rf_curve_1 = _rf_curve_editor("jt1")

    pd_opt_1, price_calc_1, expected_cf_1, pv_cf_1, discount_1, table_1 = run_jarrow_turnbull_one_pd(
        market_price=market_price_1, face_value=face_value_1, coupon_rate=coupon_rate_1,
        freq=int(freq_1), bond_years=bond_years_1, recovery_rate=recovery_1, rf=rf_curve_1,
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Calibrated flat PD", f"{pd_opt_1:.2%}")
    m2.metric("Model price (should match market)", f"{price_calc_1:.4f}")
    m3.metric("Pricing error", f"{abs(price_calc_1 - market_price_1):.6f}")
    st.dataframe(table_1.style.format("{:.4f}"), width="stretch")

with tab_jtn:
    with st.expander("Methodology", expanded=False):
        st.markdown(
            r"""
Same idea as the flat-PD model, but with one free hazard rate $PD_t$ per
coupon period instead of a single constant — a simple **term structure**
of default probabilities, calibrated so the model price matches the
market price using the same survival-weighted discounting.
"""
        )
    c1, c2, c3 = st.columns(3)
    with c1:
        market_price_2 = st.number_input("Observed market price", min_value=0.01, value=90.0, step=1.0, key="mp2")
        face_value_2 = st.number_input("Face value", min_value=0.01, value=100.0, step=10.0, key="fv2")
    with c2:
        coupon_rate_2 = st.number_input("Coupon rate (annual)", min_value=0.0, value=0.05, step=0.005, format="%.4f", key="cr2")
        freq_2 = st.number_input("Payments per year", min_value=0, value=4, step=1, key="freq2")
    with c3:
        bond_years_2 = st.number_input("Years to maturity", min_value=0.25, value=2.0, step=0.25, key="by2")
        recovery_2 = st.number_input("Recovery rate", min_value=0.0, max_value=1.0, value=0.40, step=0.05, key="rec2")

    with st.expander("Risk-free curve used for discounting"):
        rf_curve_2 = _rf_curve_editor("jtn")

    pd_opt_2, price_calc_2, expected_cf_2, pv_cf_2, discount_2, table_2 = run_jarrow_turnbull_many_pd(
        market_price=market_price_2, face_value=face_value_2, coupon_rate=coupon_rate_2,
        freq=int(freq_2), bond_years=bond_years_2, recovery_rate=recovery_2, rf=rf_curve_2,
    )

    m1, m2 = st.columns(2)
    m1.metric("Model price (should match market)", f"{price_calc_2:.4f}")
    m2.metric("Pricing error", f"{abs(price_calc_2 - market_price_2):.6f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=table_2.index, y=table_2["PD"], mode="lines+markers", name="Period PD"))
    fig.update_layout(height=320, xaxis_title="Payment date (years)", yaxis_title="Calibrated PD", yaxis_tickformat=".1%")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(table_2.style.format("{:.4f}"), width="stretch")

# ---------------------------------------------------------------------------
# Tab 4 — Credit spread bootstrap
# ---------------------------------------------------------------------------
with tab_spread:
    with st.expander("Methodology", expanded=False):
        st.markdown(
            r"""
A model-free bootstrap: compare each period's risky zero-coupon bond price
to the equivalent risk-free price to back out **cumulative survival
probability** directly from the spread, then difference across periods for
the **unconditional** (marginal, first-time) and **conditional**
(hazard-rate-style) default probabilities:
$$
\text{Price}_{\text{risky}}(t) = 100/(1+r_t)^t, \qquad
\text{Price}_{\text{riskless}}(t) = 100/(1+r_{f,t})^t
$$
$$
\text{CumSurvival}(t) = \frac{\text{Price}_{\text{risky}}(t)/\text{Price}_{\text{riskless}}(t) - \text{Recovery}}{1-\text{Recovery}}
$$
"""
        )

    n_periods = st.number_input("Number of periods", min_value=1, max_value=10, value=4, step=1)
    default_rf = [0.045, 0.04625, 0.0475, 0.04875]
    default_r = [0.05125, 0.05375, 0.05625, 0.05875]

    edit_df = pd.DataFrame({
        "Risk-free rate": (default_rf + [default_rf[-1]] * n_periods)[:n_periods],
        "Risky rate": (default_r + [default_r[-1]] * n_periods)[:n_periods],
    })
    edited = st.data_editor(edit_df, width="stretch", hide_index=True, key="spread_bootstrap_editor")
    recovery_rate_3 = st.number_input("Recovery rate (0 = zero-recovery base case)", min_value=0.0, max_value=0.99, value=0.0, step=0.05)

    result_df = analyze_credit_risk(edited["Risk-free rate"].tolist(), edited["Risky rate"].tolist(), recovery_rate=recovery_rate_3)
    st.dataframe(result_df, width="stretch")
