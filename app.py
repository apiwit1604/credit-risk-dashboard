# -*- coding: utf-8 -*-
"""Page 1 — Introduction. Entry point of the Streamlit multipage app."""
from __future__ import annotations

import streamlit as st

from src.state import init_state

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Credit Risk Dashboard — Introduction",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize global session state
init_state()

# -----------------------------------------------------------------------------
# SIDEBAR DESIGN
# -----------------------------------------------------------------------------
with st.sidebar:
    # 1. Branding Header
    st.markdown("## 🛡️ Risk Metrics")
    st.caption("Credit VaR & Analytics Suite | v1.0")
    st.divider()

    # 2. Main Navigation Group
    st.caption("📂 OVERVIEW")
    st.page_link("app.py", label="Introduction", icon="🏠")

    st.caption("📊 MODELING FRAMEWORKS")
    st.page_link("pages/1_merton_kmv.py", label="Merton–KMV CVaR", icon="📈")
    st.page_link("pages/2_creditmetrics.py", label="CreditMetrics CVaR", icon="🎲")
    st.page_link("pages/3_basel.py", label="Basel Single-Factor", icon="🏛️")

    st.caption("🔍 ANALYTICS & CALIBRATION")
    st.page_link("pages/4_comparison.py", label="Model Comparison", icon="⚖️")
    st.page_link("pages/5_pd.py", label="Probability of Default", icon="🎯")

    st.caption("⚙️ CONFIGURATION")
    st.page_link("pages/6_settings.py", label="Market Settings", icon="⚙️")

    st.divider()

    # 3. Active Portfolio Quick Status Card
    st.markdown("#### 💼 Portfolio Status")
    
    # อ่านค่าจริงจาก st.session_state หากมีข้อมูล
    portfolio = st.session_state.get("portfolio", None)
    if portfolio is not None and hasattr(portfolio, "__len__"):
        n_obligors = len(portfolio)
        total_ead = getattr(portfolio, "total_ead", None) or portfolio["ead"].sum() if "ead" in portfolio else 0
        ead_display = f"${total_ead:,.0f}" if isinstance(total_ead, (int, float)) else "N/A"
    else:
        n_obligors = "Loaded"
        ead_display = "Active"

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric(label="Obligors", value=n_obligors)
    with col_b:
        st.metric(label="Total EAD", value=ead_display)

# -----------------------------------------------------------------------------
# MAIN CONTENT
# -----------------------------------------------------------------------------
st.title("Portfolio Credit Risk Dashboard")
st.caption("Credit Value-at-Risk & Probability of Default, across three independent modeling frameworks")

st.markdown(
    """
This dashboard turns a set of standalone credit-risk models into one
interactive tool: edit a sample loan/bond portfolio once, and see how its
**Credit Value-at-Risk (Credit VaR)** and **Economic Capital** look under
three very different modeling philosophies — plus four separate ways of
estimating a single **Probability of Default (PD)**.

**Objective.** Show, side by side, *why* three textbook-standard Credit VaR
approaches (a structural Monte Carlo model, a rating-migration Monte Carlo
model, and a regulatory closed-form formula) can price the same portfolio
differently — and let you test that with your own numbers, not just the
demo data.
"""
)

st.divider()
st.subheader("How the pages fit together")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("#### Merton–KMV")
    st.markdown(
        "Structural, asset-value Monte Carlo model. A firm defaults when its "
        "simulated asset value falls below its EAD at the risk horizon."
    )
with col2:
    st.markdown("#### CreditMetrics")
    st.markdown(
        "Rating-migration Monte Carlo model. Firms are revalued under every "
        "possible future rating, weighted by simulated migration outcomes."
    )
with col3:
    st.markdown("#### Basel Single-Factor")
    st.markdown(
        "Regulatory Capital Calculation via the Closed-Form Basel II/III ASRF Formula."
    )

col4, col5 = st.columns(2)
with col4:
    st.markdown("#### Model Comparison")
    st.markdown("Runs the same portfolio through all three models above and lines up the results.")
with col5:
    st.markdown("#### Probability of Default")
    st.markdown(
        "Four independent PD estimation methods: Merton's structural model, "
        "Jarrow–Turnbull (flat and term-structure hazard rates), and a "
        "model-free bootstrap from credit spreads."
    )

st.markdown("#### Settings")
st.markdown(
    "The market/model inputs that are hard to eyeball — the rating scale, the "
    "1-year transition matrix, the risk-free curve, and the credit-spread "
    "curve. Change them here and Pages (Merton KMV CVaR, CreditMetrics CVaR, Basel Single-Factor CVaR, Model Comparison and Probability of Default) recompute against the new inputs."
)

st.divider()

st.caption(
    "Built with Streamlit, NumPy, pandas, SciPy and Plotly. "
    "Use the sidebar to navigate between pages — the portfolio you edit on "
    "any of Pages (Merton KMV CVaR, CreditMetrics CVaR, Basel Single-Factor CVaR and Model Comparison) is shared across all of them."
)
