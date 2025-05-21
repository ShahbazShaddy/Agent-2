import streamlit as st
from components.upload_component import upload_files
from components.report_viewer import display_report
from components.sidebar import render_sidebar
from utils.file_handler import save_uploaded_files
from utils.parser import parse_inputs
from utils.ai_processor import analyze_with_openai
from utils.formatter import generate_outputs
from utils.mock_data import get_sample_data
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set Streamlit page config
st.set_page_config(page_title="AI Tax Analyzer", layout="wide")

# Render sidebar
render_sidebar()

# Title
st.title("🧾 AI-Powered Tax Return Analyzer")
st.markdown("Upload your scenario and tax return files for 2023 and 2024. The AI will process them and generate a structured comparison.")

# Step 1: File Upload
uploaded_files = upload_files()

# Add demo mode checkbox to sidebar
use_demo_mode = st.sidebar.checkbox("Use Demo Mode (Sample Data)", value=False)

# Main processing logic
if uploaded_files or use_demo_mode:
    try:
        if use_demo_mode:
            st.info("🔍 Using sample data in demo mode.")
            structured_output = get_sample_data()
            output_paths = generate_outputs(structured_output)
            display_report(structured_output, output_paths)
        else:
            # Step 2: Save files locally
            input_paths = save_uploaded_files(uploaded_files)
            st.success("✅ Files uploaded and saved.")

            # Step 3: Parse inputs (JSON + DOCX)
            parsed_data = parse_inputs(input_paths)
            st.info("🔍 Parsed scenario and tax return files.")

            # Step 4: Analyze with OpenAI
            with st.spinner("🤖 Analyzing tax data with OpenAI..."):
                structured_output = analyze_with_openai(parsed_data)
                
                if isinstance(structured_output, dict) and "error" in structured_output:
                    st.error(f"Error during OpenAI analysis: {structured_output['error']}")
                    
                    # Show raw response if available for debugging
                    if "raw_response" in structured_output:
                        with st.expander("Debug Information"):
                            st.text("Raw Response Sample:")
                            st.text(structured_output["raw_response"])
                            st.text("Please check that the prompt is properly formatted to return valid JSON.")
                    
                    # Offer fallback to sample data - with unique key
                    if st.button("Use Sample Data Instead", key="fallback_button1"):
                        structured_output = get_sample_data()
                        # Generate outputs and display report with sample data
                        try:
                            output_paths = generate_outputs(structured_output)
                            display_report(structured_output, output_paths)
                        except Exception as formatter_error:
                            st.error(f"Error formatting sample data: {str(formatter_error)}")
                else:
                    st.success("✅ Analysis complete!")
                    
                    # Try to generate outputs and catch specific errors
                    try:
                        # Step 5: Generate downloadable outputs
                        output_paths = generate_outputs(structured_output)
                        # Step 6: Display structured results
                        display_report(structured_output, output_paths)
                    except Exception as formatter_error:
                        st.error(f"Error generating reports: {str(formatter_error)}")
                        # Offer fallback to sample data - with unique key
                        if st.button("Use Sample Data Instead", key="fallback_button2"):
                            structured_output = get_sample_data()
                            output_paths = generate_outputs(structured_output)
                            display_report(structured_output, output_paths)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
        
        # Offer fallback to sample data - with unique key
        if st.button("Use Sample Data Instead", key="fallback_button3"):
            structured_output = get_sample_data()
            output_paths = generate_outputs(structured_output)
            display_report(structured_output, output_paths)
else:
    st.warning("📂 Please upload all three files to proceed or enable demo mode.")

# Add footer
st.markdown("---")
st.markdown("Powered by OpenAI and Streamlit")
