# src/ui.py
import streamlit as st

def render_sidebar():
    """Render a clean, unified sidebar navigation across all Streamlit pages."""

    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
            
            .sidebar-caption {
                font-size: 0.75rem;
                color: #808495;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 2px;
            }
            
            .tight-divider {
                border-bottom: 1px solid rgba(250, 250, 250, 0.2);
                margin-top: 2px;
                margin-bottom: 24px;
            }
            
            /* ระยะห่างระหว่าง Section */
            .section-spacer {
                margin-bottom: 32px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("## Risk Analytics")
        st.caption("Portfolio Credit Risk Suite v1.0")

        # Divider ชิดข้อความหัวข้อ + เว้นระยะห่างไปเมนูถัดไป
        st.markdown('<div class="tight-divider"></div>', unsafe_allow_html=True)

        # ---------------- INTRODUCTION ----------------
        st.markdown(
            '<div class="sidebar-caption">INTRODUCTION</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="tight-divider"></div>', unsafe_allow_html=True)
        st.page_link("app.py", label="Overview & Introduction")

        st.markdown(
            '<div class="section-spacer"></div>', unsafe_allow_html=True
        )

        # ---------------- MODELING FRAMEWORKS ----------------
        st.markdown(
            '<div class="sidebar-caption">MODELING FRAMEWORKS</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="tight-divider"></div>', unsafe_allow_html=True)
        st.page_link("pages/2_Merton_KMV_CVaR.py", label="Merton–KMV CVaR")
        st.page_link("pages/3_CreditMetrics_CVaR.py", label="CreditMetrics CVaR")
        st.page_link(
            "pages/4_Basel_Single_Factor_CVaR.py",
            label="Basel Single Factor Credit VaR",
        )

        st.markdown(
            '<div class="section-spacer"></div>', unsafe_allow_html=True
        )

        # ---------------- ANALYTICS & PARAMETERS ----------------
        st.markdown(
            '<div class="sidebar-caption">ANALYTICS & PARAMETERS</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="tight-divider"></div>', unsafe_allow_html=True)
        st.page_link("pages/5_Model_Comparison.py", label="Model Comparison")
        st.page_link(
            "pages/6_Probability_of_Default.py", label="Probability of Default"
        )

        st.markdown(
            '<div class="section-spacer"></div>', unsafe_allow_html=True
        )

        # ---------------- SYSTEM CONFIGURATION ----------------
        st.markdown(
            '<div class="sidebar-caption">SYSTEM CONFIGURATION</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="tight-divider"></div>', unsafe_allow_html=True)
        st.page_link("pages/7_Settings.py", label="Settings")

        st.markdown(
            '<div class="section-spacer"></div>', unsafe_allow_html=True
        )

        # ---------------- DEVELOPER CREDIT ----------------
        st.markdown(
            '<div class="sidebar-caption">DEVELOPER & LICENSE</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="tight-divider"></div>', unsafe_allow_html=True)
        st.markdown("**Developed by:** Apiwit Oonworg")
        st.caption("© 2026 Apiwit Oonworg. All rights reserved.")
