# utils/api_requests.py
# Description: Functions for making API requests (fetching metadata).

import requests
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define a default API base URL
API_BASE_URL = "http://127.0.0.1:8080/api"

def fetch_metadata(url: str, timeout: int = 5) -> dict:
    """
    Fetch file metadata from the API.

    Args:
        url (str): The URL of the file to fetch metadata for.
        timeout (int): Timeout in seconds for the API request (default: 5).

    Returns:
        dict: The JSON response containing metadata or an error message.
    """
    try:
        logging.info(f"📡 Fetching metadata for URL: {url}")

        response = requests.get(f"{API_BASE_URL}/metadata", params={"url": url}, timeout=timeout)
        response.raise_for_status()  # Raises an error for HTTP failures (4xx, 5xx)

        # Attempt to parse JSON response
        try:
            metadata = response.json()
            logging.info(f"✅ Metadata received: {metadata}")
            return metadata
        except json.JSONDecodeError:
            logging.error("❌ API returned invalid JSON response.")
            return {"error": "Invalid JSON response from API"}

    except requests.exceptions.Timeout:
        logging.error("❌ Error: API request timed out.")
        return {"error": "Request timed out"}

    except requests.exceptions.ConnectionError:
        logging.error("❌ Error: Could not connect to the API server.")
        return {"error": "Connection failed. Please ensure the backend is running."}

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"❌ HTTP Error: {http_err}")
        return {"error": f"HTTP error: {http_err}"}

    except requests.exceptions.RequestException as req_err:
        logging.error(f"❌ API Request Error: {req_err}")
        return {"error": f"Request failed: {req_err}"}

# Example usage (only runs when executed directly)
if __name__ == "__main__":
    test_url = "https://example.com/samplefile.mp4"
    metadata = fetch_metadata(test_url)
    logging.info(f"📜 Final Metadata Output: {metadata}")
