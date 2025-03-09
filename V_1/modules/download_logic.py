import os
import threading
import logging
from urllib.parse import urlparse
from modules.file_downloader import FileDownloader

# ✅ Set up logging
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class DownloadLogic:
    def __init__(self, app):
        self.app = app
        self.download_threads = {}
        self.download_stop_flags = {}

    def start_download_with_details(self, url, file_path, category, description):
        """
        ✅ Starts a download with detailed parameters.
        """
        try:
            if not url or not file_path:
                raise ValueError("URL and file path are required.")

            folder = os.path.dirname(file_path)  # ✅ Ensure correct directory
            self._add_and_start_download(url, folder, file_path, category, description)

        except Exception as e:
            logging.error(f"Download Start Error: {e}")
            self.app.status_label.update_status(f"Error: {str(e)}", "red")

    def _add_and_start_download(
        self, url, folder, file_path, category="General", description=""
    ):
        """
        ✅ Adds the download to the table and starts it in a separate thread.
        """
        file_name = self._extract_filename(url, file_path)
        print(f"🔹 Starting download: {file_name}")

        # ✅ Ensure folder exists
        if not os.path.exists(folder):
            os.makedirs(folder)

        # ✅ Prevent duplicate downloads
        existing_files = {
            self.app.download_table.tree.item(item, "values")[
                0
            ]: self.app.download_table.tree.item(item, "values")[3]
            for item in self.app.download_table.tree.get_children()
        }

        if file_name in existing_files and existing_files[file_name] in [
            "Downloading...",
            "Starting",
        ]:
            print(f"⚠️ Skipping duplicate download for {file_name}.")
            return

        print(f"✅ Adding new download: {file_name}")

        item_id = self.app.download_table.add_row(
            file_name=file_name,
            size="Calculating...",
            progress="0%",
            status="Starting",
            time_left="Unknown",
            transfer_rate="Unknown",
            date_added="Now",
        )

        stop_flag = threading.Event()
        self.download_stop_flags[item_id] = stop_flag

        print(f"🔄 Creating download thread for {file_name}...")

        thread = threading.Thread(
            target=self._download_file,
            args=(url, folder, file_name, item_id, stop_flag),
            daemon=True,
        )
        self.download_threads[item_id] = thread
        thread.start()

        print(f"✅ Download thread started for: {file_name}")

        # ✅ Update button states after adding a download
        self.app.toolbar.update_button_states()

    def _extract_filename(self, url, file_path):
        """
        ✅ Extracts a valid filename for the download.
        """
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path) or os.path.basename(file_path)

        # ✅ Ensure the filename is unique if it's from YouTube
        if "youtube.com" in url or "youtu.be" in url:
            filename = f"video_{hash(url)}.mp4"  # Unique filename based on URL hash

        return filename if filename else "downloaded_file.mp4"

    def _download_file(self, url, folder, file_name, item_id, stop_flag):
        """
        ✅ Handles actual file download logic.
        """
        try:
            if not item_id or not self.app.download_table.tree.exists(
                item_id
            ):  # ✅ Ensure item_id exists
                print(f"⚠️ Error: Item ID {item_id} not found. Skipping UI updates.")
                return

            self.app.download_table.update_progress(
                item_id, progress="0%", status="Downloading"
            )

            def progress_callback(percent, eta, speed):
                if stop_flag.is_set():
                    raise Exception("Download stopped by user.")
                self.update_progress_callback(item_id, percent, eta, speed)

            def size_callback(file_size):
                """
                ✅ Updates the actual file size in the table, handling missing sizes.
                """
                if not file_size or file_size <= 0:
                    print(
                        f"⚠️ Warning: No valid file size detected for {file_name}. Setting to 'Unknown'."
                    )
                    self.app.download_table.update_progress(item_id, size="Unknown")
                    return

                size_text = self._format_size(file_size)
                self.app.download_table.update_progress(item_id, size=size_text)
                print(f"📦 File Size: {size_text}")

            print(f"⏳ Downloading: {file_name} from {url} ...")

            # ✅ Download file using updated logic
            downloader = FileDownloader(
                url,
                folder,
                file_name,
                stop_event=stop_flag,
                progress_callback=progress_callback,
                size_callback=size_callback,
            )
            result = downloader.download()

            if os.path.exists(result):
                print(f"✅ DOWNLOAD COMPLETE: {result}")
                self.app.status_label.update_status(
                    f"Download completed: {result}", "green"
                )
                if self.app.download_table.tree.exists(
                    item_id
                ):  # ✅ Check before updating
                    self.app.download_table.update_progress(
                        item_id, progress="100%", status="Completed"
                    )
            else:
                print(f"❌ ERROR: File not found after download: {result}")
                if self.app.download_table.tree.exists(
                    item_id
                ):  # ✅ Check before updating
                    self.app.download_table.update_progress(
                        item_id, status="Error", progress="0%"
                    )

            # ✅ Update button states after completion
            self.app.toolbar.update_button_states()

        except Exception as e:
            if stop_flag.is_set():
                self.app.status_label.update_status(
                    "Download stopped by user.", "orange"
                )
                if self.app.download_table.tree.exists(
                    item_id
                ):  # ✅ Check before updating
                    self.app.download_table.update_progress(item_id, status="Stopped")
            else:
                logging.error(f"Download Failed for {file_name}: {e}")
                self.app.status_label.update_status(f"Download failed: {str(e)}", "red")
                if self.app.download_table.tree.exists(
                    item_id
                ):  # ✅ Check before updating
                    self.app.download_table.update_progress(item_id, status="Error")

            # ✅ Update button states after error
            self.app.toolbar.update_button_states()

    def _format_size(self, size_in_bytes):
        """
        ✅ Converts bytes into human-readable format (KB, MB, GB).
        """
        try:
            size_in_bytes = float(size_in_bytes)  # ✅ Ensure it is a number
            if size_in_bytes < 1024:
                return f"{size_in_bytes} B"
            elif size_in_bytes < 1024**2:
                return f"{size_in_bytes / 1024:.2f} KB"
            elif size_in_bytes < 1024**3:
                return f"{size_in_bytes / (1024**2):.2f} MB"
            else:
                return f"{size_in_bytes / (1024**3):.2f} GB"
        except ValueError:
            logging.error(f"Invalid size format: {size_in_bytes}")
            return "Unknown size"
