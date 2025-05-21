import streamlit as st

def upload_files():
    st.sidebar.header("Upload Tax Files")
    scenario = st.sidebar.file_uploader("Upload Client Scenario (JSON)", type=["json"], key="scenario")
    tax2023 = st.sidebar.file_uploader("Upload 2023 Tax Return (DOCX)", type=["docx"], key="tax2023")
    tax2024 = st.sidebar.file_uploader("Upload 2024 Tax Return (DOCX)", type=["docx"], key="tax2024")

    if scenario and tax2023 and tax2024:
        return {"scenario": scenario, "2023": tax2023, "2024": tax2024}
    return None