import os
import yt_dlp
import re
import threading
import logging

# ✅ Set up logging
logging.basicConfig(
    filename="yt_downloader.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ✅ Default Download Folder
DOWNLOAD_DIR = os.path.join(os.getcwd(), "Downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class YouTubeDownloader:
    """
    ✅ Handles YouTube and streaming video downloads using `yt-dlp`.
    """

    def __init__(
        self,
        url,
        output_folder=DOWNLOAD_DIR,
        quality="bestvideo+bestaudio/best",
        progress_callback=None,
    ):
        self.url = url
        self.output_folder = output_folder
        self.quality = quality
        self.progress_callback = progress_callback
        self.video_title = None
        self.download_thread = None  # ✅ Store the thread object

    @staticmethod
    def sanitize_filename(filename):
        """✅ Removes special characters and enforces filename limits."""
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename).strip().replace(" ", "_")
        return filename[:200]  # Enforce filename length limit

    def update_progress(self, d):
        """✅ Updates GUI or logs with download progress."""
        if d["status"] == "downloading":
            percent = d.get("_percent_str", "0%").strip()
            eta = d.get("eta", "Unknown")

            # ✅ Convert speed to KB/s or MB/s
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
        """
        ✅ Downloads a YouTube video with error handling and progress tracking.
        """
        try:
            # ✅ Extract video info
            ydl_opts = {"quiet": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(self.url, download=False)

            self.video_title = self.sanitize_filename(video_info.get("title", "video"))

            # ✅ Define yt-dlp download options
            ydl_opts = {
                "outtmpl": os.path.join(
                    self.output_folder, f"{self.video_title}.%(ext)s"
                ),
                "format": self.quality,
                "merge_output_format": "mp4",
                "postprocessors": [
                    {"key": "FFmpegMerger"},
                    {"key": "FFmpegMetadata"},
                ],
                "progress_hooks": [self.update_progress],
                "noplaylist": True,
                "quiet": False,
                "restrictfilenames": True,
                "ignoreerrors": True,
                "retries": 5,
                "fragment-retries": 5,
                "throttledrate": "1M",  # ✅ Prevent YouTube from throttling
            }

            output_path = os.path.join(self.output_folder, f"{self.video_title}.mp4")

            # ✅ Check if the video already exists
            if os.path.exists(output_path):
                print(f"✅ Video already downloaded: {self.video_title}")
                return os.path.abspath(output_path)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            print(f"✅ YouTube Download Complete: {output_path}")
            logging.info(f"Download complete: {output_path}")
            return os.path.abspath(output_path)

        except yt_dlp.utils.DownloadError as e:
            print(f"❌ ERROR: YouTube Download failed: {e}")
            logging.error(f"YouTube Download Failed: {self.url} - {e}")
            return f"ERROR: YouTube Download failed: {e}"

        except Exception as e:
            print(f"❌ ERROR: Unexpected error: {e}")
            logging.error(f"Unexpected Error: {self.url} - {e}")
            return f"ERROR: Unexpected error: {e}"

    def start_download(self, join_thread=False):
        """✅ Starts the YouTube download in a separate thread."""
        self.download_thread = threading.Thread(target=self.download_video, daemon=True)
        self.download_thread.start()
        if join_thread:
            self.download_thread.join()  # ✅ Option to wait for the thread to finish


class YouTubePlaylistDownloader:
    """
    ✅ Handles downloading an entire YouTube playlist using `yt-dlp`.
    """

    def __init__(
        self,
        playlist_url,
        output_folder=DOWNLOAD_DIR,
        quality="bestvideo+bestaudio/best",
        progress_callback=None,
    ):
        self.playlist_url = playlist_url
        self.output_folder = output_folder
        self.quality = quality
        self.progress_callback = progress_callback
        self.download_thread = None

    def update_progress(self, d):
        """✅ Updates GUI or logs with playlist download progress."""
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
                f"📊 Playlist Progress: {percent} | Speed: {formatted_speed} | ETA: {eta} sec"
            )

            if self.progress_callback:
                self.progress_callback(percent, eta, formatted_speed)

    def download_playlist(self):
        """
        ✅ Downloads all videos from a YouTube playlist.
        """
        try:
            ydl_opts = {
                "outtmpl": os.path.join(
                    self.output_folder, "%(playlist)s/%(title)s.%(ext)s"
                ),
                "format": self.quality,
                "merge_output_format": "mp4",
                "postprocessors": [
                    {"key": "FFmpegMerger"},
                    {"key": "FFmpegMetadata"},
                ],
                "progress_hooks": [self.update_progress],
                "noplaylist": False,  # ✅ Download the full playlist
                "quiet": False,
                "restrictfilenames": True,
                "ignoreerrors": True,
                "retries": 5,
                "fragment-retries": 5,
                "throttledrate": "1M",
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.playlist_url])

            print(f"✅ YouTube Playlist Download Complete: {self.playlist_url}")
            logging.info(f"Download complete: {self.playlist_url}")

        except yt_dlp.utils.DownloadError as e:
            print(f"❌ ERROR: YouTube Playlist Download failed: {e}")
            logging.error(
                f"YouTube Playlist Download Failed: {self.playlist_url} - {e}"
            )
            return f"ERROR: YouTube Playlist Download failed: {e}"

        except Exception as e:
            print(f"❌ ERROR: Unexpected error: {e}")
            logging.error(f"Unexpected Error: {self.playlist_url} - {e}")
            return f"ERROR: Unexpected error: {e}"

    def start_download(self, join_thread=False):
        """✅ Starts the YouTube playlist download in a separate thread."""
        self.download_thread = threading.Thread(
            target=self.download_playlist, daemon=True
        )
        self.download_thread.start()
        if join_thread:
            self.download_thread.join()
