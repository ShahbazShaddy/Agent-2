import json
import logging
from utils.ai_processor import extract_tax_parameters

logger = logging.getLogger(__name__)

def parse_inputs(file):
    """Parse JSON input file and extract required parameters using OpenAI."""
    try:
        # Ensure the buffer is at the beginning
        if hasattr(file, 'seek'):
            file.seek(0)
        
        # Load the raw JSON data
        raw_json_data = json.loads(file.read().decode('utf-8'))
        
        # Use OpenAI to extract the required parameters
        logger.info("Using OpenAI to extract tax parameters from JSON")
        parameters = extract_tax_parameters(raw_json_data)
        
        # Check for errors
        if "error" in parameters:
            logger.error(f"Error extracting parameters: {parameters['error']}")
            raise ValueError(parameters["error"])
        
        logger.info(f"Successfully extracted tax parameters: {parameters}")
        return parameters
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        raise ValueError(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        logger.error(f"Error parsing inputs: {str(e)}")
        raise Exception(f"Error parsing inputs: {str(e)}")
