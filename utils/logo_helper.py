"""
Logo helper for Steel Flow Analysis Platform
Displays logo in sidebar across all pages
"""
import streamlit as st
import os


def display_sidebar_logo():
    """
    Display logo in sidebar
    Compatible with older Streamlit versions
    """
    # Path to logo (relative to utils directory)
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.jpg')

    if os.path.exists(logo_path):
        with st.sidebar:
            st.image(logo_path, use_column_width=True)
            st.markdown("---")
