# utils/helpers.py
# Description: Helper functions for URL validation and metadata fetching.

import requests
from urllib.parse import urlparse, urlunparse, urljoin
import tkinter.messagebox as messagebox
from gui.utils.api_requests import fetch_metadata  # Import API request function

def validate_url(url: str) -> bool:
    """
    Checks if a given string is a valid, reachable URL.

    Args:
        url (str): The URL string to validate.

    Returns:
        bool: True if the URL is valid and reachable, False otherwise.
    """
    url = url.strip()  # Remove leading/trailing spaces

    # 🛠 Auto-correct missing scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url  # Assume secure connection

    parsed = urlparse(url)

    # Ensure scheme and netloc exist
    if not parsed.scheme or not parsed.netloc:
        return False

    # 🛠 Check if the domain exists (basic reachability test)
    try:
        response = requests.head(url, allow_redirects=True, timeout=3)
        if response.status_code >= 400:
            return False
    except requests.RequestException:
        return False

    return True

def clean_url(url: str) -> str:
    """
    Cleans and normalizes a URL by removing unnecessary spaces and ensuring proper formatting.

    Args:
        url (str): The URL string to clean.

    Returns:
        str: Cleaned and properly formatted URL.
    """
    url = url.strip()

    # 🛠 Auto-correct missing scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url  # Assume secure connection

    return urlunparse(urlparse(url))

def get_metadata(url: str):
    """
    Fetch file metadata using the API and display errors in a messagebox if needed.

    Args:
        url (str): The URL of the file.

    Returns:
        dict: Metadata dictionary (if successful) or None (if failed).
    """
    url = clean_url(url)

    # 🛠 Validate the cleaned URL before proceeding
    if not validate_url(url):
        messagebox.showwarning("Invalid URL", "The URL provided is invalid or unreachable. Please check and try again.")
        return None

    metadata = fetch_metadata(url)

    # 🛠 Improved error handling
    if not metadata or "error" in metadata:
        error_msg = metadata.get("error", "Unknown error while fetching metadata.")
        messagebox.showwarning("Metadata Error", f"Failed to retrieve metadata: {error_msg}")
        return None

    # 🛠 Auto-fill file details if available
    return {
        "file_name": metadata.get("suggested_name", "Unknown File"),
        "file_size_kb": metadata.get("file_size", 0) // 1024 if metadata.get("file_size") else "Unknown",
        "file_type": metadata.get("file_type", "Unknown"),
    }
