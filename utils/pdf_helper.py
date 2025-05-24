import streamlit as st
import base64
import os

def display_pdf(pdf_path):
    """
    Display a PDF file in the Streamlit app.
    
    Args:
        pdf_path (str): Path to the PDF file
    """
    # Make sure the file exists
    if not os.path.exists(pdf_path):
        st.warning(f"PDF file not found: {pdf_path}")
        return
    
    # Display PDF using base64 encoding
    with open(pdf_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    # Create iframe with responsive design
    pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="800px"
            style="border: 1px solid #ddd; border-radius: 5px;"
            type="application/pdf"
        ></iframe>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)
