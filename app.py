# -*- coding: utf-8 -*-
"""Page 1 — Introduction. Entry point of the Streamlit multipage app."""
from __future__ import annotations

import streamlit as st

from src.state import init_state

st.set_page_config(
    page_title="Credit Risk Dashboard — Introduction",
    page_icon="💳",
    layout="wide",
)
init_state()

st.title("💳 Portfolio Credit Risk Dashboard")
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
    st.markdown("#### 📉 Page 2 — Merton–KMV")
    st.markdown(
        "Structural, asset-value Monte Carlo model. A firm defaults when its "
        "simulated asset value falls below its EAD at the risk horizon."
    )
with col2:
    st.markdown("#### 📊 Page 3 — CreditMetrics")
    st.markdown(
        "Rating-migration Monte Carlo model. Firms are revalued under every "
        "possible future rating, weighted by simulated migration outcomes."
    )
with col3:
    st.markdown("#### 🏦 Page 4 — Basel Single-Factor")
    st.markdown(
        "Closed-form Basel II/III ASRF formula — the regulatory capital "
        "calculation, fixed at a 99.9% confidence level by definition."
    )

col4, col5 = st.columns(2)
with col4:
    st.markdown("#### 🧮 Page 5 — Model Comparison")
    st.markdown("Runs the same portfolio through all three models above and lines up the results.")
with col5:
    st.markdown("#### 🎯 Page 6 — Probability of Default")
    st.markdown(
        "Four independent PD estimation methods: Merton's structural model, "
        "Jarrow–Turnbull (flat and term-structure hazard rates), and a "
        "model-free bootstrap from credit spreads."
    )

st.markdown("#### ⚙️ Page 7 — Settings")
st.markdown(
    "The market/model inputs that are hard to eyeball — the rating scale, the "
    "1-year transition matrix, the risk-free curve, and the credit-spread "
    "curve. Change them here and Pages 2–6 recompute against the new inputs."
)

st.divider()

with st.expander("🔧 What changed vs. the original notebook (read this if you're grading it)"):
    st.markdown(
        """
This dashboard is a refactor of a working research notebook, not a
line-for-line port. Restructuring it into a proper package surfaced a
handful of issues that were sitting quietly in the original — worth being
upfront about, since some of them change the numbers:

1. **Forward-rate bug (CreditMetrics revaluation).** The original computed
   one forward rate per coupon date inside a loop, but overwrote the same
   variable each iteration — so *every* cash flow ended up discounted with
   only the last period's rate. Fixed to discount each cash flow with its
   own maturity-matched forward rate (`src/valuation.py`).
2. **Silent parameter bug (Merton–KMV).** The simulation function took an
   `n_sims` argument but built its event-summary table off a *global*
   `n_sim` variable instead — invisible in a notebook run once with matching
   values, but wrong the moment a dashboard slider changes `n_sims` on its
   own. Fixed to use the local parameter throughout (`src/credit_var/merton_kmv.py`).
3. **Hidden import dependency.** `get_forward()` relied on `CubicSpline`
   being imported by an unrelated, later notebook cell — it only worked
   because of Colab's execution order, not the code's own structure. Every
   module now imports exactly what it uses.
4. **Basel maturity input ignored the portfolio.** The Basel ASRF formula
   hardcoded `M = 2.5` for every firm, discarding each firm's own
   `years_to_maturity` that was already sitting in the portfolio data —
   which defeats the point of Basel's maturity adjustment. Fixed to default
   to each firm's own maturity (floored/capped at 1–5 years per the IRB
   rules), with an optional override for sensitivity testing.
5. **Fragile ordering trick (Jarrow–Turnbull, flat PD).** The original built
   payment dates in descending order, then used `np.sort()` on the
   *probability* arrays as an implicit reversal — correct only by luck for
   a constant hazard rate. Rewritten to sort payment dates ascending up
   front, matching the (already-correct) approach used in the
   term-structure variant.
6. **Performance.** Two event-summary tables were built with pure-Python
   loops over every single simulation draw. Rewritten with vectorized
   NumPy/pandas operations so the sliders on Pages 2–3 stay responsive even
   at 1,000,000+ simulations.

See the [README](https://github.com) methodology section for the math
behind each model, including a couple of documented modeling
simplifications that were **not** changed (e.g. the Merton structural
solve uses a penalized single-objective heuristic rather than an exact
2-equation solve).
"""
    )

st.divider()
st.caption(
    "Built with Streamlit, NumPy, pandas, SciPy and Plotly. "
    "Use the sidebar to navigate between pages — the portfolio you edit on "
    "any of Pages 2–5 is shared across all of them."
)
