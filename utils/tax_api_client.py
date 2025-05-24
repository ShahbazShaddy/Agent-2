import os
import requests
import logging
import json
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def calculate_tax(tax_parameters):
    """
    Call the Income Tax Calculator API with the extracted parameters.
    
    Args:
        tax_parameters (dict): Dictionary containing the tax parameters
            - country: 2-letter country code (e.g., US, CA)
            - region: State/province code (e.g., CA, NY, ON)
            - income: Annual income amount (as string or number)
            - filing_status: Tax filing status (for US only)
            
    Returns:
        dict: API response containing tax calculations or error message
    """
    # Get API key from environment variables
    api_key = os.getenv("API_NINJAS_KEY")
    if not api_key:
        logger.error("API Ninjas API key not found")
        return {"error": "API Ninjas API key not found. Please check your .env file."}
    
    try:
        # Extract parameters
        country = tax_parameters.get('country', '')
        region = tax_parameters.get('region', '')
        income = str(tax_parameters.get('income', 0))
        filing_status = tax_parameters.get('filing_status', '')
        
        # Clean income - remove any non-numeric characters except decimal point
        income = ''.join(c for c in income if c.isdigit() or c == '.')
        
        # Validate required parameters
        if not country or not region or not income:
            missing = []
            if not country: missing.append("country")
            if not region: missing.append("region")
            if not income: missing.append("income")
            error_msg = f"Missing required parameters: {', '.join(missing)}"
            logger.error(error_msg)
            return {"error": error_msg}
            
        # Check if filing_status is required (for US)
        if country.upper() == "US" and not filing_status:
            logger.error("Missing required parameter: filing_status (required for US)")
            return {"error": "Missing required parameter: filing_status (required for US)"}
        
        # Construct API URL
        api_url = f'https://api.api-ninjas.com/v1/incometaxcalculator?country={country}&region={region}&income={income}'
        
        # Add filing_status for US
        if country.upper() == "US" and filing_status:
            api_url += f'&filing_status={filing_status}'
        
        logger.info(f"Calling tax calculator API with URL: {api_url}")
        
        # Make API request
        response = requests.get(api_url, headers={'X-Api-Key': api_key})
        
        # Check response
        if response.status_code == requests.codes.ok:
            try:
                # Parse JSON response
                tax_result = response.json()
                logger.info("Successfully received tax calculation result")
                
                # Check if there are any "premium subscription required" fields
                if contains_premium_fields(tax_result):
                    logger.info("Found premium subscription fields - enhancing with OpenAI")
                    enhanced_result = enhance_with_openai(tax_result, tax_parameters)
                    return enhanced_result
                
                return tax_result
            except ValueError as e:
                logger.error(f"Failed to parse API response as JSON: {e}")
                return {"error": f"Invalid API response: {e}", "raw_response": response.text}
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return {"error": f"API error: {response.status_code}", "message": response.text}
            
    except Exception as e:
        logger.error(f"Error calculating taxes: {str(e)}")
        return {"error": f"Error calculating taxes: {str(e)}"}

def contains_premium_fields(tax_result):
    """Check if any field in the response contains 'premium subscription required'"""
    result_str = json.dumps(tax_result)
    return "premium subscription required" in result_str.lower()

def enhance_with_openai(tax_result, tax_parameters):
    """
    Use OpenAI to enhance tax results by replacing "premium subscription required" with realistic dummy values
    
    Args:
        tax_result (dict): Original API response with premium subscription notices
        tax_parameters (dict): Original tax parameters used to inform OpenAI
        
    Returns:
        dict: Enhanced tax calculation with reasonable dummy values
    """
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found - cannot enhance tax results")
        return tax_result  # Return original result if OpenAI is not available
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Create a prompt for OpenAI
        prompt = f"""
        Below is a tax calculation result that contains some fields marked as "premium subscription required".
        Please replace these fields with realistic dummy values based on the provided tax parameters.
        
        Tax Parameters:
        - Country: {tax_parameters.get('country')}
        - Region: {tax_parameters.get('region')}
        - Income: {tax_parameters.get('income')}
        - Filing Status: {tax_parameters.get('filing_status', 'Not specified')}
        - Deductions: {tax_parameters.get('deductions', 0)}
        - Credits: {tax_parameters.get('credits', 0)}
        - Self-employed: {tax_parameters.get('self_employed', False)}
        
        Tax Calculation Result:
        ```
        {json.dumps(tax_result, indent=2)}
        ```
        
        Please provide a complete JSON object that keeps all existing numeric values intact and ONLY replaces
        "premium subscription required" strings with realistic numeric values or appropriate text.
        
        For numeric fields like tax rates, effective rates, or tax amounts, use realistic values based on:
        1. The provided income level
        2. The specified country and region tax laws
        3. The filing status
        
        Return ONLY a valid JSON object with all "premium subscription required" values replaced.
        """
        
        # Call OpenAI API
        logger.info("Calling OpenAI to enhance tax calculation results")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Using a faster model for this task
            messages=[
                {"role": "system", "content": "You are a tax calculation assistant. Your task is to replace premium subscription placeholders with realistic dummy values in tax API responses."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2  # Low temperature for more consistent results
        )
        
        # Extract content
        content = response.choices[0].message.content
        
        # Parse the JSON response
        try:
            # Find JSON in the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                enhanced_result = json.loads(json_content)
                
                # Add a note that some values are AI-generated estimates
                enhanced_result["note"] = "Some values in this response were estimated by AI as they require a premium subscription in the original API."
                
                logger.info("Successfully enhanced tax calculation with OpenAI")
                return enhanced_result
            else:
                logger.error("Could not find valid JSON in OpenAI response")
                return tax_result  # Return original result if parsing fails
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in OpenAI response: {e}")
            return tax_result  # Return original result if parsing fails
            
    except Exception as e:
        logger.error(f"Error enhancing tax results with OpenAI: {str(e)}")
        return tax_result  # Return original result if OpenAI enhancement fails
