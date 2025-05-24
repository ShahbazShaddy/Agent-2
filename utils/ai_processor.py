import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from utils.mock_data import get_sample_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def analyze_with_openai(parsed):
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found")
        return {"error": "OpenAI API key not found. Please check your .env file."}
    
    # Load the prompt template
    try:
        with open("templates/tax_comparison_prompt.txt", "r") as f:
            prompt_template = f.read()
    except Exception as e:
        logger.error(f"Failed to load prompt template: {str(e)}")
        return {"error": f"Failed to load prompt template: {str(e)}"}
    
    # Format the prompt
    try:
        # Log the data being used to format the prompt
        logger.info("--- Client Scenario Data for OpenAI ---")
        logger.info(json.dumps(parsed['scenario'], indent=2))
        logger.info("--- 2023 Tax Return Data for OpenAI ---")
        logger.info(parsed['tax_return_2023'])
        logger.info("--- 2024 Tax Return Data for OpenAI ---")
        logger.info(parsed['tax_return_2024'])
        logger.info("--------------------------------------")

        prompt = prompt_template.replace("{{SCENARIO}}", json.dumps(parsed['scenario'], indent=2))
        prompt = prompt.replace("{{TAX_RETURN_2023}}", parsed['tax_return_2023'])
        prompt = prompt.replace("{{TAX_RETURN_2024}}", parsed['tax_return_2024'])
        
        # Log data sizes for debugging
        logger.info(f"Scenario size: {len(json.dumps(parsed['scenario']))} chars")
        logger.info(f"Tax 2023 size: {len(parsed['tax_return_2023'])} chars")
        logger.info(f"Tax 2024 size: {len(parsed['tax_return_2024'])} chars")
        logger.info(f"Total prompt size: {len(prompt)} chars")
        logger.debug(f"Prompt being sent to OpenAI (first 500 chars): {prompt[:500]}")
    except Exception as e:
        logger.error(f"Failed to format prompt: {str(e)}")
        return {"error": f"Failed to format prompt: {str(e)}"}

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        logger.info("Calling OpenAI API using ReAct framework...")
        
        # Call OpenAI API with the ReAct approach
        response = client.chat.completions.create(
            model="gpt-4", # Or use OPENAI_MODEL from constants if defined
            messages=[
                {"role": "system", "content": "You are a meticulous tax analysis assistant using the ReAct (Reasoning and Acting) framework. First reason about the tax data by explicitly analyzing patterns, anomalies, and financial implications. Then act by extracting specific financial data into a structured JSON format. Your output should include both reasoning and the final structured data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        # Extract content
        content = response.choices[0].message.content
        logger.info(f"Received response from OpenAI, length: {len(content)} chars")
        
        # Process the response to separate reasoning and structured data
        try:
            # Parse the response - extract the JSON part and reasoning part
            logger.info("Processing ReAct response to separate reasoning and structured data...")
            
            # Look for JSON array in the response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                logger.info(f"Found JSON array from index {start_idx} to {end_idx}")
                json_content = content[start_idx:end_idx]
                reasoning_content = content[:start_idx].strip()
                
                # Parse the JSON part
                structured_data = json.loads(json_content)
                
                # Basic validation
                if not isinstance(structured_data, list):
                    logger.error(f"Response is not a JSON array: {type(structured_data)}")
                    return {"error": "Response is not a JSON array", "raw_response": content[:200]}
                
                if len(structured_data) == 0:
                    logger.error("Response JSON array is empty")
                    return {"error": "Received empty JSON array", "raw_response": content[:200]}
                    
                logger.info(f"Successfully parsed JSON array with {len(structured_data)} items")
                
                # Validate all items have required fields
                missing_fields = False
                for i, item in enumerate(structured_data):
                    if not all(k in item for k in ["type", "2023", "2024", "difference"]):
                        missing_fields = True
                        logger.error(f"Item {i} missing required fields: {item}")
                
                if missing_fields:
                    return {"error": "JSON items missing required fields", "raw_response": content[:200]}
                
                # Return both the structured data and the reasoning
                return {
                    "structured_data": structured_data,
                    "reasoning": reasoning_content
                }
            else:
                # If we can't find JSON array brackets, treat as error
                logger.error("Could not find valid JSON array in response")
                return {
                    "error": "Could not find valid JSON array in response",
                    "raw_response": content[:200] + "..." if len(content) > 200 else content
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                "error": f"Invalid JSON in response: {str(e)}",
                "raw_response": content[:200] + "..." if len(content) > 200 else content
            }
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return {"error": f"OpenAI API error: {str(e)}"}

def extract_tax_parameters(json_data):
    """Extract required tax parameters from JSON using OpenAI with enhanced intelligence across all parameters"""
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found")
        return {"error": "OpenAI API key not found. Please check your .env file."}
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        logger.info("Calling OpenAI API to extract tax parameters with comprehensive analysis...")
        
        # Create a prompt for extraction with detailed instructions for ALL parameters
        prompt = f"""
        Perform a comprehensive tax analysis on the provided JSON data. Extract and calculate the following parameters:
        
        1. COUNTRY (2-letter country code, e.g., US, CA):
           - Convert full names like "United States" to "US"
           - Look for country information in client details, address information, or tax form references
        
        2. REGION (state/province code, e.g., CA, NY, ON):
           - Convert full names like "California" to "CA"
           - Check for state information in addresses, tax calculations, or state-specific tax references
        
        3. INCOME (annual total income):
           - Thoroughly search for ALL potential income sources throughout the JSON
           - For US tax purposes, include these income sources in your calculation:
             * Wages, salaries, tips
             * Interest income (taxable)
             * Dividend income
             * Business income (Schedule C)
             * Capital gains
             * Rental income
             * Royalties
             * Retirement income (pensions, annuities, IRA distributions)
             * Social Security benefits (taxable portion)
             * Unemployment compensation
             * Other income sources reported on Form 1040
           - If multiple income sources are found, SUM them to calculate total income
           - Convert any monthly income to annual (multiply by 12)
           - Clean numeric values by removing "$" and "," characters
        
        4. FILING_STATUS (for US only, e.g., single, married, head_of_household):
           - Look for explicit filing status mentions
           - If not explicitly stated, infer from context (e.g., mentions of spouse, dependents)
           - Only required for US taxpayers
        
        5. DEDUCTIONS (total tax deductions):
           - Search for ALL potential deduction types:
             * Standard deduction references
             * Itemized deduction mentions
             * Mortgage interest deduction
             * State and local tax deductions
             * Property tax deductions
             * Medical expense deductions
             * Charitable contribution deductions
             * Other itemized deductions
             * Above-the-line deductions
           - Calculate total based on available information or client's situation
           - If unclear whether standard or itemized, choose based on what's most advantageous
        
        6. CREDITS (total tax credits):
           - Search for ALL potential tax credits:
             * Child tax credit
             * Earned income credit
             * Education credits
             * Child and dependent care credit
             * Retirement savings credit
             * Foreign tax credit
             * Energy credits
             * Other credits referenced
           - Sum all applicable credits
        
        7. SELF_EMPLOYED (boolean):
           - Look for direct mentions of self-employment
           - Check for business income, Schedule C references, or self-employment tax mentions
           - Set to true if any evidence of self-employment is found
        
        8. ADDITIONAL RELEVANT TAX DATA:
           - Identify property information that might be tax-relevant
           - Note retirement account information
           - Capture home mortgage details if present
           - Note dependents information
           - Identify any tax strategies mentioned
           - Extract investment details relevant to taxation
        
        Provide a comprehensive, thoughtful analysis that considers the entirety of the JSON data. Make reasonable inferences when information is implicit rather than explicit. Your goal is to extract maximum useful tax information.
        
        Return ONLY a valid JSON object with these keys and their calculated values:
        - "country" (required)
        - "region" (required)
        - "income" (required)
        - "filing_status" (required for US)
        - "deductions" (numeric value or 0 if not found)
        - "credits" (numeric value or 0 if not found)
        - "self_employed" (boolean)
        - "income_sources" (object with breakdown of income sources)
        - "deduction_details" (object with breakdown of deductions)
        - "credit_details" (object with breakdown of credits)
        - "additional_tax_details" (object with other relevant tax information)
        
        JSON data to analyze:
        ```
        {json.dumps(json_data)}
        ```
        """
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4", # Using GPT-4 for comprehensive analysis
            messages=[
                {"role": "system", "content": "You are a tax professional with expertise in US and international tax law. Your task is to extract and calculate all relevant tax parameters from JSON data, providing a comprehensive tax analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        # Extract content
        content = response.choices[0].message.content
        logger.info(f"Received comprehensive tax analysis from OpenAI, length: {len(content)} chars")
        
        # Parse the JSON response
        try:
            # Find JSON in the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                parameters = json.loads(json_content)
                
                # Basic validation
                required_params = ["country", "region", "income"]
                for param in required_params:
                    if param not in parameters:
                        return {"error": f"Missing required parameter: {param}"}
                
                # If US, validate filing_status
                if parameters.get("country", "").upper() == "US" and "filing_status" not in parameters:
                    return {"error": "Missing required parameter: filing_status (required for US)"}
                    
                # Set defaults for optional parameters
                parameters.setdefault("deductions", 0)
                parameters.setdefault("credits", 0)
                parameters.setdefault("self_employed", False)
                
                # Log the identified sources if available
                if "income_sources" in parameters:
                    logger.info(f"Income sources identified: {parameters['income_sources']}")
                if "deduction_details" in parameters:
                    logger.info(f"Deduction details identified: {parameters['deduction_details']}")
                if "credit_details" in parameters:
                    logger.info(f"Credit details identified: {parameters['credit_details']}")
                
                logger.info(f"Successfully extracted comprehensive tax parameters")
                return parameters
            else:
                logger.error("Could not find valid JSON in OpenAI response")
                return {"error": "Could not extract parameters from response", "raw_response": content[:200]}
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {"error": f"Invalid JSON in response: {str(e)}", "raw_response": content[:200]}
            
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return {"error": f"OpenAI API error: {str(e)}"}