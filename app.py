import streamlit as st
import json
from components.upload_component import upload_files
from components.sidebar import render_sidebar
from utils.parser import parse_inputs
from utils.tax_api_client import calculate_tax
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set Streamlit page config
st.set_page_config(page_title="Agent 2", layout="wide")

# Render sidebar
render_sidebar()

# Title
st.title("🧾 Agent 2")
st.markdown("Upload your tax parameters JSON file. OpenAI will extract parameters and calculate taxes.")

# File Upload
uploaded_files = upload_files()

# Main processing logic
if uploaded_files:
    try:
        with st.spinner("🤖 Analyzing tax parameters with OpenAI..."):
            # Parse the JSON file using OpenAI
            tax_parameters = parse_inputs(uploaded_files["tax_parameters"])
            
            # Print parameters to terminal (keep this for debugging)
            print("\n===== EXTRACTED TAX PARAMETERS =====")
            print(f"Country: {tax_parameters['country']}")
            print(f"Region: {tax_parameters['region']}")
            print(f"Income: {tax_parameters['income']}")
            
            if tax_parameters['country'].upper() == "US":
                print(f"Filing Status: {tax_parameters['filing_status']}")
            
            print(f"Deductions: {tax_parameters['deductions']}")
            print(f"Credits: {tax_parameters['credits']}")
            print(f"Self-employed: {tax_parameters['self_employed']}")
            
            # Print additional details if available
            if "income_sources" in tax_parameters:
                print("\nIncome Sources:")
                for source, amount in tax_parameters["income_sources"].items():
                    print(f"  - {source}: {amount}")
            
            if "deduction_details" in tax_parameters:
                print("\nDeduction Details:")
                for deduction, amount in tax_parameters["deduction_details"].items():
                    print(f"  - {deduction}: {amount}")
            
            if "credit_details" in tax_parameters:
                print("\nCredit Details:")
                for credit, amount in tax_parameters["credit_details"].items():
                    print(f"  - {credit}: {amount}")
                    
            if "additional_tax_details" in tax_parameters:
                print("\nAdditional Tax Information:")
                for key, value in tax_parameters["additional_tax_details"].items():
                    print(f"  - {key}: {value}")
                    
            print("===================================\n")
            
            # Just show a simple success message instead of detailed visualizations
            st.success("✅ Tax parameters extracted successfully")
        
        # Calculate taxes using the API
        with st.spinner("💰 Calculating taxes with API..."):
            tax_calculation = calculate_tax(tax_parameters)
            
            # Print tax calculation results to terminal
            if "error" not in tax_calculation:
                print("\n===== TAX CALCULATION RESULTS =====")
                print(json.dumps(tax_calculation, indent=2))
                print("===================================\n")
                
                # Display in Streamlit - Enhanced readable format
                st.success("✅ Tax calculation completed successfully")
                st.subheader("Tax Calculation Results")
                
                # Create multiple sections with well-formatted information
                col1, col2 = st.columns(2)
                
                # Column 1 - Basic information
                with col1:
                    st.markdown("### 📋 Tax Summary")
                    
                    # Format income data
                    income = tax_calculation.get('income', 0)
                    st.metric("Total Income", f"${income:,.2f}" if isinstance(income, (int, float)) else income)
                    
                    # Format taxable income
                    taxable_income = tax_calculation.get('taxable_income', 0)
                    st.metric("Taxable Income", f"${taxable_income:,.2f}" if isinstance(taxable_income, (int, float)) else taxable_income)
                    
                    # Format deductions
                    deductions = tax_calculation.get('deductions', 0)
                    st.metric("Total Deductions", f"${deductions:,.2f}" if isinstance(deductions, (int, float)) else deductions)
                    
                    # Format federal tax rate
                    fed_rate = tax_calculation.get('federal_effective_rate', 0)
                    if isinstance(fed_rate, (int, float)):
                        if fed_rate < 1:  # Check if it's in decimal form
                            fed_rate_display = f"{fed_rate * 100:.2f}%"
                        else:
                            fed_rate_display = f"{fed_rate:.2f}%"
                        st.metric("Federal Tax Rate", fed_rate_display)
                    
                    # Format federal taxes
                    fed_tax = tax_calculation.get('federal_taxes_owed', 0)
                    st.metric("Federal Taxes", f"${fed_tax:,.2f}" if isinstance(fed_tax, (int, float)) else fed_tax)
                
                # Column 2 - Additional tax information
                with col2:
                    st.markdown("### 💵 Tax Obligations")
                    
                    # Format state/region taxes
                    region_tax = tax_calculation.get('region_taxes_owed', 0)
                    st.metric("State/Region Tax", f"${region_tax:,.2f}" if isinstance(region_tax, (int, float)) else region_tax)
                    
                    # Format other taxes
                    if 'fica_total' in tax_calculation:
                        fica_tax = tax_calculation.get('fica_total', 0)
                        st.metric("FICA Tax", f"${fica_tax:,.2f}" if isinstance(fica_tax, (int, float)) else fica_tax)
                    
                    # Format total taxes
                    total_tax = tax_calculation.get('total_taxes_owed', 0)
                    st.metric("Total Tax", f"${total_tax:,.2f}" if isinstance(total_tax, (int, float)) else total_tax)
                    
                    # Format after-tax income
                    after_tax = tax_calculation.get('income_after_tax', 0)
                    st.metric("After-Tax Income", f"${after_tax:,.2f}" if isinstance(after_tax, (int, float)) else after_tax)
                    
                    # Format total effective tax rate
                    total_rate = tax_calculation.get('total_effective_tax_rate', 0)
                    if isinstance(total_rate, (int, float)):
                        if total_rate < 1:  # Check if it's in decimal form
                            total_rate_display = f"{total_rate * 100:.2f}%"
                        else:
                            total_rate_display = f"{total_rate:.2f}%"
                        st.metric("Total Effective Tax Rate", total_rate_display)
                
                # Add option to upload previous year's tax return for comparison
                st.subheader("📊 Compare with Previous Year")
                st.write("Upload your previous year's tax return to see a comparison.")
                previous_tax_return = st.file_uploader("Upload previous year's tax return (PDF/JSON/DOCX)", 
                                                  type=["pdf", "json", "docx"], 
                                                  key="previous_tax_return")
                
                # If previous year's tax return uploaded, generate comparison
                if previous_tax_return is not None:
                    with st.spinner("🔄 Analyzing and comparing tax returns..."):
                        from utils.tax_comparison import parse_previous_tax_return, generate_tax_comparison
                        from utils.pdf_helper import display_pdf
                        import datetime
                        
                        # Process the previous year's tax return
                        previous_year_data = parse_previous_tax_return(previous_tax_return)
                        
                        if "error" not in previous_year_data:
                            # Generate comparison report
                            comparison_result = generate_tax_comparison(
                                previous_year_data=previous_year_data,
                                current_year_data=tax_calculation,
                                client_data=tax_parameters
                            )
                            
                            if "error" not in comparison_result:
                                st.success("✅ Tax comparison completed!")
                                
                                # Display comparison report download button
                                with open(comparison_result["report_path"], "rb") as file:
                                    st.download_button(
                                        label="📥 Download Tax Comparison Report (PDF)",
                                        data=file,
                                        file_name=f"Tax_Comparison_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                                        mime="application/pdf"
                                )
                                
                                # Display PDF in UI
                                try:
                                    display_pdf(comparison_result["report_path"])
                                except Exception as e:
                                    st.warning(f"Unable to display PDF in browser: {str(e)}. Please download using the button above.")
                            else:
                                st.error(f"Error generating comparison: {comparison_result['error']}")
                        else:
                            st.error(f"Error processing previous tax return: {previous_year_data['error']}")

                # Raw JSON data in expander
                with st.expander("View Raw Tax Calculation JSON"):
                    st.json(tax_calculation)
            else:
                print(f"\nError calculating taxes: {tax_calculation.get('error')}")
                if "message" in tax_calculation:
                    print(f"Message: {tax_calculation.get('message')}")
                st.error(f"Error calculating taxes: {tax_calculation.get('error')}")
                if "message" in tax_calculation:
                    st.error(f"API message: {tax_calculation.get('message')}")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        st.error(f"An error occurred: {str(e)}")
else:
    st.warning("📂 Please upload a tax parameters JSON file to proceed.")

# Add footer
st.markdown("---")
st.markdown("Agent 2 powered by OpenAI and API Ninjas")
