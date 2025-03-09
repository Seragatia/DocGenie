# utils/file_ops.py
# Description: Utility functions for file operations.

import os
import json
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Lock for file operations to prevent race conditions
file_lock = threading.Lock()

def get_default_download_path() -> str:
    """
    Returns the default download directory based on the operating system.

    Returns:
        str: The absolute path to the user's download folder.
    """
    try:
        if os.name == 'nt':  # Windows
            return os.path.join(os.environ.get("USERPROFILE", "C:\\Users\\Default"), "Downloads")
        else:  # macOS/Linux
            return os.path.join(os.environ.get("HOME", "/home/default"), "Downloads")
    except KeyError:
        logging.warning("⚠️ Could not determine default download path. Using current directory.")
        return os.getcwd()  # Fallback: Use current working directory if env vars fail

def create_folder_if_not_exists(folder_path: str) -> None:
    """
    Creates a folder if it doesn't already exist.

    Args:
        folder_path (str): Path of the folder to create.
    """
    try:
        os.makedirs(folder_path, exist_ok=True)
        logging.info(f"📁 Folder ensured: {folder_path}")
    except Exception as e:
        logging.error(f"❌ Error creating folder '{folder_path}': {e}")

def ensure_unique_filename(file_path: str) -> str:
    """
    Ensures the file name is unique by appending '_copy' if a file with the same name exists.

    Args:
        file_path (str): The intended file path.

    Returns:
        str: A unique file path.
    """
    if not os.path.exists(file_path):
        return file_path

    base, ext = os.path.splitext(file_path)
    counter = 1

    while os.path.exists(file_path):
        file_path = f"{base}_copy{counter}{ext}"
        counter += 1

    return file_path

def save_download_info(download_info: dict, filename: str = "downloads.json") -> None:
    """
    Saves the download information to a JSON file.

    Args:
        download_info (dict): The download details (URL, save_path, etc.).
        filename (str): The filename to save the data (default: downloads.json).
    """
    download_path = get_default_download_path()
    create_folder_if_not_exists(download_path)

    file_path = os.path.join(download_path, filename)

    with file_lock:  # Prevent concurrent write issues
        try:
            # Read existing downloads
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    try:
                        data = json.load(file)
                        if not isinstance(data, list):  # Ensure it's a list
                            logging.warning(f"⚠️ Invalid JSON format in {filename}. Resetting file.")
                            data = []
                    except json.JSONDecodeError:
                        logging.warning(f"⚠️ Corrupted JSON in {filename}. Resetting file.")
                        data = []
            else:
                data = []

            # Validate and ensure the save path is unique
            if "save_path" in download_info:
                download_info["save_path"] = ensure_unique_filename(download_info["save_path"])

            # Append new download info
            data.append(download_info)

            # Save back to file
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            
            logging.info(f"✅ Download info saved: {file_path}")

        except Exception as e:
            logging.error(f"❌ Error saving download info: {e}")

def save_failed_download(download_info: dict, filename: str = "failed_downloads.json") -> None:
    """
    Saves failed download attempts to a separate JSON file.

    Args:
        download_info (dict): The download details including failure reason.
        filename (str): The filename to save the failed downloads (default: failed_downloads.json).
    """
    download_path = get_default_download_path()
    create_folder_if_not_exists(download_path)

    file_path = os.path.join(download_path, filename)

    with file_lock:
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    try:
                        data = json.load(file)
                        if not isinstance(data, list):
                            data = []
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []

            data.append(download_info)

            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4)
            
            logging.info(f"❌ Failed download logged: {file_path}")

        except Exception as e:
            logging.error(f"❌ Error logging failed download: {e}")

# Example usage:
if __name__ == "__main__":
    test_download = {
        "url": "https://example.com/file.mp4",
        "save_path": get_default_download_path() + "/file.mp4",
        "status": "Completed"
    }
    save_download_info(test_download)
