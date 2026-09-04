import streamlit as st

st.set_page_config(page_title="Credit Risk Toolkit", page_icon="📊", layout="wide")

st.title("📊 Credit Risk Toolkit")
st.caption("Reduced-form, structural, simulation-based, and regulatory credit-risk models — one page per model, math alongside the numbers.")

st.warning(
    "⚠️ **Before comparing numbers across pages:** the KMV and Basel pages use a different "
    "'asset correlation' convention (R = ρ²) than the Credit VaR — Ratings Migration page (ρ directly). "
    "See the note at the bottom of both pages, or `docs/06_correlation_conventions.md` in the repo.",
    icon="⚠️",
)

st.markdown("### Pick a model from the sidebar. Here's what each one does:")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Reduced-form (bond-implied PD)")
    st.markdown(
        "- **Bond-Implied PD — Credit Spread**: PD from the ratio of a risky "
        "vs. riskless bond price at each maturity.\n"
        "- **Bond-Implied PD — Price Calibration**: solves for the PD (flat, "
        "or a full term structure) that reprices an observed market bond."
    )

    st.markdown("#### Structural")
    st.markdown(
        "- **Merton Structural Model**: single-firm PD from equity value & "
        "volatility, treating equity as a call option on firm assets.\n"
        "- **KMV Portfolio Monte Carlo**: the same idea, simulated across a "
        "correlated portfolio to get VaR / CVaR / Economic Capital."
    )

with col2:
    st.markdown("#### Simulation-based portfolio Credit VaR")
    st.markdown(
        "- **Credit VaR — Ratings Migration**: CreditMetrics-style model — "
        "simulates full rating *migrations* (not just default) and revalues "
        "each position on its new credit curve."
    )

    st.markdown("#### Regulatory")
    st.markdown(
        "- **Basel Single-Factor Capital**: the closed-form IRB / ASRF "
        "formula banks actually use for minimum regulatory capital — no "
        "simulation needed, but assumes an infinitely granular portfolio."
    )

st.divider()
st.markdown(
    "Full mathematical derivations for every model live in `docs/` in the "
    "repository — each dashboard page links to its corresponding doc."
)
