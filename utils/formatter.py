import json
import pandas as pd
from fpdf import FPDF
import os
import datetime
import logging

logger = logging.getLogger(__name__)

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_outputs(structured_output):
    """Generate PDF, Excel, and JSON outputs from the structured data"""
    try:
        # Validate input
        if not structured_output:
            raise ValueError("No data received for output generation")
            
        if not isinstance(structured_output, list):
            raise ValueError(f"Expected list but got {type(structured_output)}")
            
        if len(structured_output) == 0:
            raise ValueError("Received empty data list")
        
        # Ensure all items have required fields
        for item in structured_output:
            if not isinstance(item, dict):
                raise ValueError(f"Expected dict but got {type(item)}")
            if not all(k in item for k in ["type", "2023", "2024", "difference"]):
                raise ValueError(f"Missing required fields in item: {item}")
                
        # Create timestamp for unique filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_path = f"{OUTPUT_DIR}/output_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(structured_output, f, indent=2)
        
        # Create DataFrame - add index to prevent "all scalar values" error
        df = pd.DataFrame(structured_output).reset_index(drop=True)
        
        # Save Excel with better formatting
        excel_path = f"{OUTPUT_DIR}/summary_comparison_{timestamp}.xlsx"
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Tax Comparison', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Tax Comparison']
            
            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'bg_color': '#D7E4BC',
                'border': 1
            })
            
            # Format headers
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Set column widths
            worksheet.set_column('A:A', 40)  # Type column
            worksheet.set_column('B:D', 15)  # Value columns
                
        # Generate PDF with category grouping
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Comprehensive Tax Comparison Report", 0, 1, "C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 6, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
        pdf.ln(5)
        
        # Organize data by categories
        category_groups = {
            "PERSONAL INFORMATION": [],
            "INCOME": [],
            "ADJUSTMENTS": [],
            "DEDUCTIONS": [],
            "TAX CALCULATION": [],
            "CREDITS": [],
            "PAYMENTS": [],
            "FINAL OUTCOMES": [],
            "OTHER": []
        }
        
        # Sort items into categories
        for item in structured_output:
            category_type = item["type"]
            
            # Determine which group this item belongs to
            assigned = False
            for group_name, prefixes in [
                ("PERSONAL INFORMATION", ["FILING", "DEPENDENT"]),
                ("INCOME", ["WAGES", "INTEREST", "DIVIDEND", "BUSINESS", "CAPITAL", "RENTAL", "TOTAL_INCOME"]),
                ("ADJUSTMENTS", ["IRA_DEDUCTION", "STUDENT", "SELF_EMPLOYED", "HEALTH", "ADJUSTMENT", "ADJUSTED_GROSS"]),
                ("DEDUCTIONS", ["MEDICAL", "STATE", "TAX", "MORTGAGE", "CHARITABLE", "DEDUCTION"]),
                ("TAX CALCULATION", ["TAXABLE", "LIABILITY", "ALTERNATIVE", "CALCULATION"]),
                ("CREDITS", ["CREDIT"]),
                ("PAYMENTS", ["WITHHELD", "ESTIMATED", "PAYMENT", "REFUND"]),
                ("FINAL OUTCOMES", ["TOTAL_TAX", "OVERPAYMENT", "REFUND", "AMOUNT_OWED", "EFFECTIVE", "MARGINAL"])
            ]:
                if any(prefix in category_type.upper() for prefix in prefixes):
                    category_groups[group_name].append(item)
                    assigned = True
                    break
            
            # If not assigned to any specific group, put in OTHER
            if not assigned:
                category_groups["OTHER"].append(item)
        
        # Function to draw table header
        def draw_table_header():
            pdf.set_font("Arial", "B", 10)
            pdf.set_fill_color(220, 220, 220)
            pdf.cell(70, 8, "Category", 1, 0, "L", True)
            pdf.cell(30, 8, "2023 ($)", 1, 0, "C", True)
            pdf.cell(30, 8, "2024 ($)", 1, 0, "C", True)
            pdf.cell(30, 8, "Difference ($)", 1, 1, "C", True)
            pdf.set_font("Arial", "", 9)
        
        # Draw each category group
        for group_name, items in category_groups.items():
            if items:  # Only show categories with data
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, group_name, 0, 1, "L")
                
                draw_table_header()
                
                # Add data rows
                pdf.set_font("Arial", "", 9)
                for item in items:
                    # Format the category name for display (replace underscores with spaces, capitalize)
                    display_name = item["type"].replace("_", " ").title()
                    
                    # If the name is too long, handle it to prevent overflow
                    if len(display_name) > 40:
                        display_name = display_name[:37] + "..."
                    
                    pdf.cell(70, 7, display_name, 1)
                    
                    # Format numbers with commas for thousands
                    pdf.cell(30, 7, f"${item['2023']:,}", 1, 0, "R")
                    pdf.cell(30, 7, f"${item['2024']:,}", 1, 0, "R")
                    
                    # Format difference with + or - sign and color
                    diff = item["difference"]
                    if diff > 0:
                        diff_text = f"+${diff:,}"
                        pdf.set_text_color(0, 128, 0)  # Green for positive
                    elif diff < 0:
                        diff_text = f"-${abs(diff):,}"
                        pdf.set_text_color(255, 0, 0)  # Red for negative
                    else:
                        diff_text = "$0"
                        pdf.set_text_color(0, 0, 0)  # Black for zero
                        
                    pdf.cell(30, 7, diff_text, 1, 1, "R")
                    pdf.set_text_color(0, 0, 0)  # Reset text color
                
                pdf.ln(5)
        
        # Add summary statistics at the end
        try:
            agi_2023 = next((item['2023'] for item in structured_output if item['type'].upper() == 'ADJUSTED_GROSS_INCOME'), 0)
            agi_2024 = next((item['2024'] for item in structured_output if item['type'].upper() == 'ADJUSTED_GROSS_INCOME'), 0)
            total_tax_2023 = next((item['2023'] for item in structured_output if item['type'].upper() == 'TOTAL_TAX'), 0)
            total_tax_2024 = next((item['2024'] for item in structured_output if item['type'].upper() == 'TOTAL_TAX'), 0)
            
            if agi_2023 > 0 or agi_2024 > 0:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Tax Burden Summary", 0, 1, "L")
                pdf.set_font("Arial", "", 10)
                
                effective_rate_2023 = (total_tax_2023 / agi_2023 * 100) if agi_2023 > 0 else 0
                effective_rate_2024 = (total_tax_2024 / agi_2024 * 100) if agi_2024 > 0 else 0
                
                pdf.cell(70, 8, "Adjusted Gross Income", 1)
                pdf.cell(30, 8, f"${agi_2023:,}", 1, 0, "R")
                pdf.cell(30, 8, f"${agi_2024:,}", 1, 0, "R")
                pdf.cell(30, 8, f"${agi_2024 - agi_2023:,}", 1, 1, "R")
                
                pdf.cell(70, 8, "Total Tax", 1)
                pdf.cell(30, 8, f"${total_tax_2023:,}", 1, 0, "R")
                pdf.cell(30, 8, f"${total_tax_2024:,}", 1, 0, "R")
                pdf.cell(30, 8, f"${total_tax_2024 - total_tax_2023:,}", 1, 1, "R")
                
                pdf.cell(70, 8, "Effective Tax Rate", 1)
                pdf.cell(30, 8, f"{effective_rate_2023:.2f}%", 1, 0, "R")
                pdf.cell(30, 8, f"{effective_rate_2024:.2f}%", 1, 0, "R")
                pdf.cell(30, 8, f"{effective_rate_2024 - effective_rate_2023:.2f}%", 1, 1, "R")
        except Exception as e:
            logger.warning(f"Could not generate summary statistics: {e}")
        
        pdf_path = f"{OUTPUT_DIR}/tax_report_{timestamp}.pdf"
        pdf.output(pdf_path)
        
        return {
            "json": json_path,
            "excel": excel_path,
            "pdf": pdf_path
        }
    except Exception as e:
        logger.error(f"Error generating outputs: {str(e)}")
        raise Exception(f"Error generating outputs: {str(e)}")
