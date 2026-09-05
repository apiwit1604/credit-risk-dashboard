# src/ui.py
import streamlit as st

def render_sidebar():
    """Render a clean, unified sidebar navigation across all Streamlit pages."""
    
    # CSS สำหรับซ่อน Default Multi-page Navigation ของ Streamlit
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("## Risk Analytics")
        st.caption("Portfolio Credit Risk Suite v1.0")
        st.divider()

        # Navigation
        st.caption("INTRODUCTION")
        st.page_link("app.py", label="Overview & Introduction")
        st.divider()

        st.caption("MODELING FRAMEWORKS")
        st.page_link("pages/2_Merton_KMV_CVaR.py", label="Merton–KMV CVaR")
        st.page_link("pages/3_CreditMetrics_CVaR.py", label="CreditMetrics CVaR")
        st.page_link("pages/4_Basel_Single_Factor_CVaR.py", label="Basel Single Factor Credit VaR")
        st.divider()

        st.caption("ANALYTICS & PARAMETERS")
        st.page_link("pages/5_Model_Comparison.py", label="Model Comparison")
        st.page_link("pages/6_Probability_of_Default.py", label="Probability of Default")
        st.divider()

        st.caption("SYSTEM CONFIGURATION")
        st.page_link("pages/7_Settings.py", label="Settings")
        st.divider()

        # Developer Credit & License
        st.caption("DEVELOPER & LICENSE")
        st.markdown("**Developed by:** Apiwit Oonworg")
        st.caption("© 2026 Apiwit Oonworg. All rights reserved.")
