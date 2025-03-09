# utils/api_requests.py
# Description: Functions for making API requests (e.g., file metadata, download actions) from the Rust backend.

import requests
import logging
import json

# Configure logging (if not configured elsewhere)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define a default API base URL (points to your Rust server, which by default listens on port 8080)
API_BASE_URL = "http://127.0.0.1:8080/api"

def fetch_metadata(url: str, timeout: int = 5) -> dict:
    """
    Fetch file metadata from the Rust backend's /metadata endpoint via POST.

    The Rust endpoint expects a JSON payload like:
        { "url": "https://example.com/samplefile.mp4" }

    Args:
        url (str): The URL of the file to fetch metadata for.
        timeout (int): Timeout in seconds for the API request (default: 5).

    Returns:
        dict: The JSON response containing metadata or an error message.
    """
    try:
        logging.info(f"📡 Fetching metadata for URL: {url}")
        response = requests.post(
            f"{API_BASE_URL}/metadata",
            json={"url": url},
            timeout=timeout
        )
        response.raise_for_status()  # Raises an HTTPError for 4xx/5xx statuses

        try:
            metadata = response.json()
            logging.info(f"✅ Metadata received: {metadata}")
            return metadata
        except json.JSONDecodeError:
            logging.error("❌ API returned invalid JSON response.")
            return {"error": "Invalid JSON response from backend."}

    except requests.exceptions.Timeout:
        logging.error("❌ Error: API request timed out.")
        return {"error": "Request timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        logging.error("❌ Error: Could not connect to the API server.")
        return {"error": "Connection failed. Is the backend running?"}
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"❌ HTTP Error: {http_err}")
        return {"error": f"HTTP error: {http_err}"}
    except requests.exceptions.RequestException as req_err:
        logging.error(f"❌ API Request Error: {req_err}")
        return {"error": f"Request failed: {req_err}"}

def start_download(task_info: dict, timeout: int = 5) -> dict:
    """
    Starts a new download by POSTing to the /download endpoint.
    Expects a JSON body like:
      { 
        "id": "<optional>",
        "url": "<the download URL>",
        "destination": "<where to save>",
        "status": "<ignored here>",
        "progress": 0.0,
        "segments": <int - optional>
      }

    Args:
        task_info (dict): The new task data (including 'url', 'destination', etc.).
        timeout (int): The request timeout in seconds.

    Returns:
        dict: JSON response, e.g. { "message": "Download started", "task_id": "..." }
    """
    try:
        logging.info(f"📡 Starting download with info: {task_info}")
        response = requests.post(
            f"{API_BASE_URL}/download",
            json=task_info,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error starting download: {e}")
        return {"error": str(e)}

def get_download_status(task_id: str, timeout: int = 5) -> dict:
    """
    Retrieves the status of a specific download task from /download/{id}.

    Args:
        task_id (str): The download task ID.
        timeout (int): The request timeout.

    Returns:
        dict: The JSON response containing the task info or an error.
    """
    try:
        logging.info(f"📡 Getting status for task_id: {task_id}")
        response = requests.get(
            f"{API_BASE_URL}/download/{task_id}",
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error fetching download status: {e}")
        return {"error": str(e)}

def pause_download(task_id: str, timeout: int = 5) -> dict:
    """
    Pauses a specific download task by calling POST /download/{id}/pause.

    Args:
        task_id (str): The download task ID.
        timeout (int): The request timeout.

    Returns:
        dict: JSON response with success or error message.
    """
    try:
        logging.info(f"📡 Pausing download task_id: {task_id}")
        response = requests.post(
            f"{API_BASE_URL}/download/{task_id}/pause",
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error pausing download: {e}")
        return {"error": str(e)}

def resume_download(task_id: str, timeout: int = 5) -> dict:
    """
    Resumes a specific download task by calling POST /download/{id}/resume.

    Args:
        task_id (str): The download task ID.
        timeout (int): The request timeout.

    Returns:
        dict: JSON response with success or error message.
    """
    try:
        logging.info(f"📡 Resuming download task_id: {task_id}")
        response = requests.post(
            f"{API_BASE_URL}/download/{task_id}/resume",
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error resuming download: {e}")
        return {"error": str(e)}

def cancel_download(task_id: str, timeout: int = 5) -> dict:
    """
    Cancels a download task by calling POST /download/{id}/cancel.

    Args:
        task_id (str): The download task ID.
        timeout (int): The request timeout.

    Returns:
        dict: JSON response with success or error message.
    """
    try:
        logging.info(f"📡 Canceling download task_id: {task_id}")
        response = requests.post(
            f"{API_BASE_URL}/download/{task_id}/cancel",
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error canceling download: {e}")
        return {"error": str(e)}

def list_downloads(timeout: int = 5) -> dict:
    """
    Lists all current download tasks by calling GET /downloads.

    Args:
        timeout (int): The request timeout.

    Returns:
        dict: JSON array or an error dict if something went wrong.
    """
    try:
        logging.info("📡 Listing all downloads...")
        response = requests.get(f"{API_BASE_URL}/downloads", timeout=timeout)
        response.raise_for_status()
        return response.json()  # a list of tasks
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error listing downloads: {e}")
        return {"error": str(e)}

# Example usage (only runs if we do `python api_requests.py` directly)
if __name__ == "__main__":
    # 1) Test metadata fetch
    test_url = "https://example.com/samplefile.mp4"
    metadata = fetch_metadata(test_url)
    logging.info(f"📜 Final Metadata Output: {metadata}")

    # 2) Test starting a download (dummy data for demonstration)
    new_task_info = {
        "id": "",  # let server auto-generate or specify a custom ID
        "url": "https://example.com/file.zip",
        "destination": "/path/to/output/file.zip",
        "status": "pending",
        "progress": 0.0,
        "segments": 2  # try segmented if you want
    }
    start_response = start_download(new_task_info)
    logging.info(f"🚀 Start Download Response: {start_response}")

    # 3) Possibly check status or list all tasks
    all_tasks = list_downloads()
    logging.info(f"📝 All tasks: {all_tasks}")
