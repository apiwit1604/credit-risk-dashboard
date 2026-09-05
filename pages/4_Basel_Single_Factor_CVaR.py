# -*- coding: utf-8 -*-
"""Page 4 — Basel II/III Asymptotic Single Risk Factor (ASRF) Credit VaR."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from src.compute import cached_basel, cached_transition_matrix_n
from src.state import init_state
from src.ui_components import render_model_portfolio_editor

st.set_page_config(page_title="Basel Single-Factor Credit VaR", page_icon="🏦", layout="wide")
init_state()

st.title("Basel Single-Factor (ASRF) Credit VaR")

with st.expander("Methodology", expanded=False):
    st.markdown(
        r"""
Unlike the two Monte Carlo models, this is the **closed-form** regulatory
capital formula behind Basel II/III's corporate IRB approach — no
simulation, fixed at a **99.9% confidence level by regulation**, not a
user choice.

**Asset correlation** (Basel's corporate formula):
$$
R(PD) = 0.12\cdot\frac{1-e^{-50\,PD}}{1-e^{-50}} + 0.24\cdot\left(1-\frac{1-e^{-50\,PD}}{1-e^{-50}}\right)
$$

**Maturity adjustment**, with $b(PD) = \big(0.11852 - 0.05478\ln PD\big)^2$
and effective maturity $M$ (floored/capped at 1–5 years):
$$
MA(PD, M) = \frac{1 + (M-2.5)\,b(PD)}{1 - 1.5\,b(PD)}
$$

**Worst-Case Default Rate** at 99.9%:
$$
WCDR(PD) = \Phi\!\left(\frac{\Phi^{-1}(PD) + \sqrt{R}\,\Phi^{-1}(0.999)}{\sqrt{1-R}}\right)
$$

**Capital requirement / Economic Capital** and **Expected Loss**:
$$
K = \big(LGD\cdot WCDR(PD) - PD\cdot LGD\big)\cdot MA(PD,M), \qquad
EC = K \times EAD, \qquad EL = PD \times LGD \times EAD
$$
        """
    )
    st.info(
        "**Correction applied here:** the original notebook hardcoded M = 2.5 for "
        "every firm. This version defaults M to each firm's own `years_to_maturity` "
        "(the Basel maturity adjustment only means something if M reflects the "
        "exposure's actual remaining life) — toggle back to a flat M below to compare.",
        icon="🔧",
    )

st.subheader("Portfolio")
render_model_portfolio_editor(
    "basel", key="portfolio_editor_basel",
    caption="Only the fields the Basel formula reads: Firm, Rating, EAD, LGD. "
            "Asset value/correlation/coupon are edited on the other Credit VaR pages.",
)
portfolio = st.session_state["portfolio"]

st.subheader("Model settings")
c1, c2, c3 = st.columns(3)
with c1:
    st.session_state["loss_horizon"] = st.number_input(
        "Loss horizon for the transition matrix (years)", min_value=0.08, max_value=5.0,
        value=float(st.session_state["loss_horizon"]), step=0.25,
        help="Shared with Pages 2 and 3 — drives the 1-year-PD used in the Basel formula.",
        key="horizon_basel",
    )
with c2:
    st.session_state["basel_use_firm_maturity"] = st.toggle(
        "Use each firm's own maturity (recommended)",
        value=st.session_state["basel_use_firm_maturity"],
    )
with c3:
    if not st.session_state["basel_use_firm_maturity"]:
        st.session_state["basel_maturity_override"] = st.number_input(
            "Flat maturity M for every firm (years)", min_value=1.0, max_value=5.0,
            value=float(st.session_state["basel_maturity_override"]), step=0.5,
        )
    else:
        st.caption(
            "Maturity (M) taken from each firm's `years_to_maturity` (clipped to Basel's [1, 5] range) — "
            "that field isn't shown on this page's table, but it's the same shared firm record you can "
            "edit on the CreditMetrics or Model Comparison page."
        )

st.caption("Confidence level: **99.9%** (fixed by the Basel IRB framework — not adjustable).")

if not portfolio:
    st.warning("Add at least one firm to the portfolio to run the model.")
    st.stop()

rating_labels = st.session_state["rating_labels"]
transition_matrix_n = cached_transition_matrix_n(
    st.session_state["transition_matrix"], rating_labels, st.session_state["loss_horizon"]
)
maturity_override = None if st.session_state["basel_use_firm_maturity"] else float(st.session_state["basel_maturity_override"])

try:
    results = cached_basel(portfolio, transition_matrix_n, maturity_override)
except KeyError as exc:
    st.error(
        f"Every firm's rating must exist in the rating scale ({', '.join(rating_labels)}). "
        f"Missing: {exc}. Check the portfolio table or the Settings page."
    )
    st.stop()

st.subheader("Results")
m1, m2, m3 = st.columns(3)
m1.metric("Expected Loss", f"{results['expected_loss']:,.2f}")
m2.metric("CVaR (Total Risk, 99.9%)", f"{results['var']:,.2f}")
m3.metric("Capital Requirement (Economic Capital)", f"{results['economic_capital']:,.2f}")

left, right = st.columns([3, 2])
with left:
    st.markdown("**Per-firm breakdown**")
    table = results["results"].copy()
    for col in ["PD", "Correlation", "WCDR"]:
        table[col] = table[col].map(lambda x: f"{x:.3%}")
    for col in ["Expected Loss", "Capital Requirement", "CVaR (Total Risk)"]:
        table[col] = table[col].map(lambda x: f"{x:,.2f}")
    st.dataframe(table, width="stretch", hide_index=True)
with right:
    st.markdown("**Capital requirement by firm**")
    raw = results["results"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=raw["Firm Name"], y=raw["Expected Loss"], name="Expected Loss", marker_color="#72B7B2"))
    fig.add_trace(go.Bar(x=raw["Firm Name"], y=raw["Capital Requirement"], name="Capital Requirement", marker_color="#F58518"))
    fig.update_layout(barmode="stack", height=380, yaxis_title="Amount")
    st.plotly_chart(fig, width="stretch")
