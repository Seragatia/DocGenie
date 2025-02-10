import os
import requests
from urllib.parse import urlparse

def download_file(url, output_folder, stop_event=None, progress_callback=None):
    """
    Downloads a file with support for stopping and progress tracking.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    file_name = os.path.basename(urlparse(url).path) or "downloaded_file"
    output_path = os.path.join(output_folder, file_name)

    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            file_size = int(response.headers.get('content-length', 0))

            with open(output_path, "wb") as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if stop_event and stop_event.is_set():
                        raise InterruptedError("Download stopped by user.")
                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress_callback and file_size:
                        percent = f"{(downloaded / file_size * 100):.2f}%"
                        progress_callback(percent, "Unknown", f"{downloaded / 1024:.2f} KB/s")

        return os.path.basename(output_path)

    except InterruptedError:
        if os.path.exists(output_path):
            os.remove(output_path)
        return "Download stopped by user."

    except requests.RequestException as e:
        return f"Error downloading file: {e}"
