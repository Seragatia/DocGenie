import yt_dlp
import os


def download_video(
    url, output_folder, quality="bestvideo+bestaudio/best", stop_event=None, progress_callback=None
):
    """
    Downloads a video using yt-dlp with support for stopping and progress tracking.

    Args:
        url (str): The URL of the video to download.
        output_folder (str): The folder where the video will be saved.
        quality (str): The desired quality format (default is "bestvideo+bestaudio/best").
        stop_event (threading.Event): Event to signal stopping the download.
        progress_callback (callable): A callback function for progress updates.
    
    Returns:
        str: The downloaded file name or an error message.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_template = os.path.join(output_folder, "%(title)s.%(ext)s")

    options = {
        'outtmpl': output_template,
        'format': quality,
        'progress_hooks': [lambda d: progress_hook(d, stop_event, progress_callback)],
        'continuedl': True,  # Resume partially downloaded files
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)
        return os.path.basename(file_name)

    except InterruptedError:
        clean_partial_files(output_folder)
        return "Download stopped by user."

    except Exception as e:
        return f"Error downloading video: {e}"


def progress_hook(d, stop_event, progress_callback):
    """
    Handles progress updates for video downloads.

    Args:
        d (dict): Progress information dictionary from yt-dlp.
        stop_event (threading.Event): Event to signal stopping the download.
        progress_callback (callable): A callback function for progress updates.
    """
    if stop_event and stop_event.is_set():
        raise InterruptedError("Download stopped by user.")

    if d['status'] == 'downloading' and progress_callback:
        percent = d.get('_percent_str', '0%').strip()
        eta = d.get('eta', 'Unknown')
        speed = d.get('_speed_str', 'Unknown')
        progress_callback(percent, eta, speed)


def clean_partial_files(output_folder):
    """
    Removes any partially downloaded files.

    Args:
        output_folder (str): The folder to scan for partial files.
    """
    for f in os.listdir(output_folder):
        if f.endswith(".part"):
            try:
                os.remove(os.path.join(output_folder, f))
            except Exception as e:
                print(f"Error removing file {f}: {e}")
