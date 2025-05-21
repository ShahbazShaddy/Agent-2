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
        # Log the beginning of the prompt to verify content
        logger.debug(f"Prompt being sent to OpenAI (first 500 chars): {prompt[:500]}")
        # For more detailed debugging, you might want to log the full prompt,
        # but be cautious if it contains sensitive data or is very long.
        # logger.info(f"Full prompt for OpenAI:\n{prompt}") 
    except Exception as e:
        logger.error(f"Failed to format prompt: {str(e)}")
        return {"error": f"Failed to format prompt: {str(e)}"}

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        logger.info("Calling OpenAI API...")
        
        # Call OpenAI API without response_format parameter (not supported by all models)
        response = client.chat.completions.create(
            model="gpt-4", # Or use OPENAI_MODEL from constants if defined
            messages=[
                {"role": "system", "content": "You are a meticulous tax analysis assistant. Your primary task is to extract specific financial data fields from the provided text documents (scenario and tax returns) and structure this extracted data into a JSON array, following the user's detailed instructions. You must ONLY output the JSON array and nothing else."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
            # Removed response_format parameter as it's not supported by the model
        )
        
        # Extract content
        content = response.choices[0].message.content
        logger.info(f"Received response from OpenAI, length: {len(content)} chars")
        
        # Clean the content to ensure it's valid JSON
        content = content.strip()
        
        # Handle potential text wrapping of JSON
        if not (content.startswith('[') and content.endswith(']')):
            logger.warning("Response doesn't start with [ and end with ], attempting to fix...")
            # Try to extract the JSON part
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                logger.info(f"Found JSON array from index {start_idx} to {end_idx}")
                content = content[start_idx:end_idx]
            else:
                # If we can't find JSON array brackets, treat as error
                logger.error("Could not find valid JSON array in response")
                return {
                    "error": "Could not find valid JSON array in response",
                    "raw_response": content[:200] + "..." if len(content) > 200 else content
                }
        
        # Try to parse the JSON
        try:
            logger.info("Parsing JSON response...")
            result = json.loads(content)
            
            # Basic validation
            if not isinstance(result, list):
                logger.error(f"Response is not a JSON array: {type(result)}")
                return {"error": "Response is not a JSON array", "raw_response": content[:200]}
            
            if len(result) == 0:
                logger.error("Response JSON array is empty")
                return {"error": "Received empty JSON array", "raw_response": content[:200]}
                
            logger.info(f"Successfully parsed JSON array with {len(result)} items")
            
            # Validate all items have required fields
            missing_fields = False
            for i, item in enumerate(result):
                if not all(k in item for k in ["type", "2023", "2024", "difference"]):
                    missing_fields = True
                    logger.error(f"Item {i} missing required fields: {item}")
            
            if missing_fields:
                return {"error": "JSON items missing required fields", "raw_response": content[:200]}
            
            # All validation passed, return the result
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                "error": f"Invalid JSON in response: {str(e)}",
                "raw_response": content[:200] + "..." if len(content) > 200 else content
            }
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return {"error": f"OpenAI API error: {str(e)}"}