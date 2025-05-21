import streamlit as st

def render_sidebar():
    st.sidebar.title("Comprehensive Tax Analysis")
    st.sidebar.markdown("---")
    st.sidebar.title("Navigation")
    st.sidebar.markdown("Upload files and view AI-generated comprehensive tax comparison reports.")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## How to use")
    st.sidebar.markdown("""
    1. Upload your client scenario (JSON)
    2. Upload 2023 tax return (DOCX)
    3. Upload 2024 tax return (DOCX)
    4. Wait for AI to process the data
    5. View the comprehensive comparison
    6. Download the detailed reports
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.info("This tool analyzes ALL details in tax returns, not just tax calculations. It compares income, deductions, credits, and all other information between tax years.")
