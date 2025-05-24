import streamlit as st

def upload_files():
    st.sidebar.header("Upload Tax Parameters")
    tax_parameters = st.sidebar.file_uploader("Upload Tax Parameters (JSON)", type=["json"], key="tax_parameters")

    if tax_parameters:
        return {"tax_parameters": tax_parameters}
    return None