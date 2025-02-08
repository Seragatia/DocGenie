import yt_dlp
import os
import requests
from urllib.parse import urlparse


def download_video(url, output_folder, quality="bestvideo+bestaudio/best", stop_event=None, progress_callback=None):
    """
    Downloads a video using yt-dlp with support for stopping and progress tracking.
    """
    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_template = os.path.join(output_folder, "%(title)s.%(ext)s")

    options = {
        'outtmpl': output_template,
        'format': quality,
        'noprogress': False,  # Allow progress updates
        'progress_hooks': [lambda d: progress_hook(d, stop_event, progress_callback)],
        'continuedl': True,  # Resume partially downloaded files
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            # Download the video and get metadata
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        return os.path.basename(file_name)  # Return the downloaded file name

    except InterruptedError:
        clean_partial_files(output_folder)
        return "Download stopped by user."

    except Exception as e:
        return f"Error downloading video: {e}"


def progress_hook(d, stop_event, progress_callback):
    """
    Handles progress updates and stops download if requested.
    """
    if stop_event and stop_event.is_set():
        raise InterruptedError("Download stopped by user.")

    try:
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            eta = d.get('eta', 'Unknown')
            speed = d.get('_speed_str', 'Unknown')

            # Call external callback (for UI updates)
            if progress_callback:
                progress_callback(percent, eta, speed)
    except KeyError as e:
        print(f"Missing key in progress_hook: {e}")


def clean_partial_files(output_folder):
    """
    Removes any partially downloaded files after a stop.
    """
    for f in os.listdir(output_folder):
        if f.endswith(".part"):
            try:
                os.remove(os.path.join(output_folder, f))
            except Exception as e:
                print(f"Error removing file {f}: {e}")


def download_file(url, output_folder, stop_event=None, progress_callback=None):
    """
    Downloads a file with support for stopping and progress tracking.
    """
    try:
        # Ensure the output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        file_name = os.path.basename(urlparse(url).path) or "downloaded_file"
        output_path = os.path.join(output_folder, file_name)

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

                    # Calculate progress
                    percent = f"{(downloaded / file_size * 100):.2f}%" if file_size else "Unknown"
                    eta = "Unknown"
                    speed = f"{downloaded / 1024:.2f} KB/s"

                    # Call external callback (for UI updates)
                    if progress_callback:
                        progress_callback(percent, eta, speed)

        return os.path.basename(output_path)  # Return the downloaded file name

    except InterruptedError:
        if os.path.exists(output_path):
            os.remove(output_path)
        return "Download stopped by user."

    except requests.RequestException as e:
        return f"Error downloading file: {e}"


def download(url, output_folder, file_type="video", quality="bestvideo+bestaudio/best", stop_event=None, progress_callback=None):
    """
    Unified function to download videos or other files.
    """
    if file_type == "video":
        return download_video(url, output_folder, quality, stop_event, progress_callback)
    elif file_type == "file":
        return download_file(url, output_folder, stop_event, progress_callback)
    else:
        return "Invalid file_type. Please specify 'video' or 'file'."
