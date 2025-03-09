import os
import requests
import logging
import time
import yt_dlp
import re
import threading
from urllib.parse import urlparse

# ✅ Logging Setup
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ✅ Default Download Folder
DOWNLOAD_DIR = os.path.join(os.getcwd(), "Downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)


def sanitize_filename(filename):
    """✅ Remove special characters and enforce filename limits."""
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)  # Replace unsafe characters
    filename = filename.strip().replace(" ", "_")  # Replace spaces
    return (
        filename[:200] if os.name != "nt" else filename[:120]
    )  # Enforce OS filename limits


class FileDownloader:
    """✅ Handles direct file downloads with resumption support."""

    def __init__(
        self,
        url,
        output_folder=DOWNLOAD_DIR,
        file_name=None,
        stop_event=None,
        progress_callback=None,
    ):
        self.url = url
        self.output_folder = output_folder
        self.file_name = sanitize_filename(
            file_name or os.path.basename(urlparse(url).path) or "downloaded_file"
        )
        self.file_path = os.path.join(output_folder, self.file_name)
        self.stop_event = stop_event or threading.Event()
        self.progress_callback = progress_callback
        self.chunk_size = 16384  # ✅ Optimized for efficient downloading
        self.downloaded = 0
        self.total_size = 0
        self.retries = 3
        self.retry_delay = 2  # ✅ Implements exponential backoff

    def update_progress(self, percent, speed, eta):
        """✅ Sends progress updates to the UI or logs."""
        if self.progress_callback:
            self.progress_callback(f"{percent:.2f}%", f"{speed:.1f} KB/s", f"{eta} sec")

    def download(self):
        """✅ Handles the file download with retry support and resumption."""
        headers = {}

        # ✅ Resume download if file exists
        if os.path.exists(self.file_path):
            self.downloaded = os.path.getsize(self.file_path)
            headers["Range"] = f"bytes={self.downloaded}-"

        for attempt in range(1, self.retries + 1):
            try:
                print(
                    f"🔍 DEBUG: Downloading {self.url} (Attempt {attempt}/{self.retries})"
                )

                with requests.get(
                    self.url, headers=headers, stream=True, timeout=15
                ) as response:
                    response.raise_for_status()
                    self.total_size = (
                        int(response.headers.get("content-length", 0)) + self.downloaded
                    )

                    start_time = time.time()
                    with open(self.file_path, "ab") as f:
                        for chunk in response.iter_content(chunk_size=self.chunk_size):
                            if self.stop_event.is_set():
                                logging.info(f"Download stopped: {self.file_name}")
                                return "Download stopped by user."

                            f.write(chunk)
                            self.downloaded += len(chunk)

                            elapsed = max(time.time() - start_time, 1)
                            speed = (
                                (self.downloaded / 1024) / elapsed if elapsed > 0 else 0
                            )
                            percent = (
                                (self.downloaded / self.total_size) * 100
                                if self.total_size
                                else 0
                            )
                            eta = (
                                ((self.total_size - self.downloaded) / (speed * 1024))
                                if speed > 0
                                else "Calculating..."
                            )

                            self.update_progress(percent, speed, eta)

                logging.info(f"Download complete: {self.file_name}")
                return os.path.abspath(self.file_path)

            except requests.RequestException as e:
                logging.error(
                    f"Download Failed: {self.url} - {e} (Attempt {attempt}/{self.retries})"
                )
                if attempt == self.retries:
                    return f"ERROR: Download failed after {self.retries} attempts: {e}"

                print(f"🔄 Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                self.retry_delay *= 2  # ✅ Exponential backoff

    def start_download(self):
        """✅ Starts the download in a separate thread."""
        threading.Thread(target=self.download, daemon=True).start()


# ✅ YouTube Video Downloader using yt-dlp
class YouTubeDownloader:
    """✅ Handles YouTube and streaming video downloads using `yt-dlp`."""

    def __init__(self, url, output_folder=DOWNLOAD_DIR, progress_callback=None):
        self.url = url
        self.output_folder = output_folder
        self.progress_callback = progress_callback
        self.video_title = None
        self.download_path = None

    def update_progress(self, d):
        """✅ Updates GUI or logs with download progress."""
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "0%").strip()
            eta = d.get("eta", "Unknown")

            speed_str = d.get("_speed_str", "Unknown")
            try:
                speed_value = (
                    float(re.findall(r"\d+\.\d+", speed_str)[0])
                    if re.findall(r"\d+\.\d+", speed_str)
                    else 0.0
                )
                speed_unit = "KB/s" if "KiB/s" in speed_str else "MB/s"
            except ValueError:
                speed_value, speed_unit = 0.0, "KB/s"

            formatted_speed = f"{speed_value:.1f} {speed_unit}"
            print(
                f"📊 YT-DLP Progress: {percent} | Speed: {formatted_speed} | ETA: {eta} sec"
            )

            if self.progress_callback:
                self.progress_callback(percent, eta, formatted_speed)

    def download_video(self):
        """✅ Downloads a YouTube video with error handling and progress tracking."""
        try:
            ydl_opts = {
                "outtmpl": os.path.join(self.output_folder, "%(title)s.%(ext)s"),
                "format": "bestvideo+bestaudio/best",
                "progress_hooks": [self.update_progress],
                "noplaylist": True,
                "quiet": False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                self.video_title = sanitize_filename(info.get("title", "video"))
                self.download_path = os.path.join(
                    self.output_folder, f"{self.video_title}.mp4"
                )

            logging.info(f"Download complete: {self.download_path}")
            return os.path.abspath(self.download_path)

        except yt_dlp.utils.DownloadError as e:
            logging.error(f"YouTube Download Failed: {self.url} - {e}")
            return f"ERROR: YouTube Download failed: {e}"

    def start_download(self):
        """✅ Starts the YouTube download in a new thread."""
        threading.Thread(target=self.download_video, daemon=True).start()
