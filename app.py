import requests
import json
import os
import logging
from typing import Optional # For type hinting Optional[str] if using Python < 3.10

# --- Configuration ---

# Set up basic logging to provide informative output
# The level can be adjusted (e.g., logging.DEBUG for more detail)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants for configuration
# Fetch model name from environment variable 'OLLAMA_MODEL' set by entrypoint.sh,
# defaulting to 'llama2' if not explicitly set.
MODEL_NAME: str = os.getenv("OLLAMA_MODEL", "llama2")
OLLAMA_HOST: str = "http://localhost:11434"  # Ollama runs on localhost within the container
API_ENDPOINT: str = f"{OLLAMA_HOST}/api/generate"
REQUEST_TIMEOUT: int = 180  # Extended timeout in seconds for potentially slow model responses

# --- Ollama Interaction ---

def query_ollama(prompt: str, model: str = MODEL_NAME) -> Optional[str]:
    """
    Sends a prompt to the configured Ollama model via its API.

    Args:
        prompt: The text prompt to send to the language model.
        model: The name of the Ollama model to use (e.g., 'llama2', 'mistral').
               Defaults to the MODEL_NAME constant.

    Returns:
        The text response from the model as a string if successful, otherwise None.
    """
    logging.info(f"Sending prompt to Ollama model '{model}' at {API_ENDPOINT}")
    # Log only the beginning of the prompt for brevity if it's long
    prompt_snippet = f"'{prompt[:80]}...'" if len(prompt) > 80 else f"'{prompt}'"
    logging.info(f"Prompt: {prompt_snippet}")

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,  # We want the full response at once, not a stream of chunks
    }

    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        # Raise an exception for HTTP errors (e.g., 404 Not Found, 500 Internal Server Error)
        response.raise_for_status()

    except requests.exceptions.Timeout:
        logging.error(f"Request timed out after {REQUEST_TIMEOUT} seconds.")
        return None
    except requests.exceptions.ConnectionError:
        logging.error(f"Could not connect to Ollama server at {OLLAMA_HOST}. "
                      "Ensure Ollama is running and accessible.")
        return None
    except requests.exceptions.RequestException as e:
        # Catch other potential request errors (like invalid URL, SSL errors etc.)
        logging.error(f"An error occurred during the API request: {e}")
        return None

    # If the request was successful, try to parse the JSON response
    try:
        data = response.json()
        response_text = data.get('response') # Use .get() for safer dictionary access

        if response_text:
            logging.info(f"Successfully received response from model '{model}'.")
            # .strip() removes leading/trailing whitespace often included in responses
            return response_text.strip()
        else:
            # Handle cases where the API call succeeded but the expected data isn't there
            logging.warning("Ollama API responded successfully, but the 'response' key was missing or empty.")
            logging.debug(f"Full response JSON: {data}") # Log full data only if needed (DEBUG level)
            return None
    except json.JSONDecodeError:
        logging.error("Failed to decode the JSON response from the Ollama API.")
        logging.debug(f"Raw response text: {response.text}") # Log raw text only if needed (DEBUG level)
        return None
    except Exception as e:
        # Catch any other unexpected errors during response processing
        logging.exception(f"An unexpected error occurred while processing the response: {e}")
        return None


if __name__ == "__main__":
    # This block ensures the following code only runs when the script is executed directly
    # (not when imported as a module).
    logging.info("Starting Python application...")
    print(query_ollama("Approximately how many books are you aware of that you could accurately list title, author, isbn, genres, and characters? Do not list them, just approximate the number."))
    logging.info("Python application finished.")
