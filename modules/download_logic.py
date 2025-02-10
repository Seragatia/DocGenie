import os
import threading
from modules.yt_downloader import download_video
from modules.file_downloader import download_file


class DownloadLogic:
    def __init__(self, app):
        self.app = app

    def start_download(self):
        """
        Handles starting a new download.
        """
        try:
            url = self.app.url_input.get_url()
            folder = self.app.url_input.get_output_folder()

            if not url or not folder:
                raise ValueError("URL or output folder is empty.")

            self._add_and_start_download(url, folder)

        except ValueError as ve:
            self.app.update_status(f"Error: {ve}", "red")
        except Exception as e:
            self.app.update_status(f"Unexpected Error: {str(e)}", "red")

    def start_download_with_details(self, url, file_path, category, description):
        """
        Starts a download with detailed parameters.
        Args:
            url (str): The URL to download.
            file_path (str): The path to save the file.
            category (str): The download category.
            description (str): The description of the download.
        """
        try:
            if not url or not file_path:
                raise ValueError("URL and file path are required.")

            folder = os.path.dirname(file_path)
            self._add_and_start_download(url, folder, file_path, category, description)

        except ValueError as ve:
            self.app.update_status(f"Error: {ve}", "red")
        except Exception as e:
            self.app.update_status(f"Unexpected Error: {str(e)}", "red")

    def _add_and_start_download(self, url, folder, file_path=None, category="General", description=""):
        """
        Adds the download to the table and starts the download in a separate thread.
        Args:
            url (str): The URL to download.
            folder (str): The folder to save the download.
            file_path (str): Optional, the full file path.
            category (str): The download category.
            description (str): The download description.
        """
        file_name = os.path.basename(file_path) if file_path else os.path.basename(url)
        item = self.app.download_table.add_row(
            file_name=file_name,
            size="Calculating...",
            progress="0%",
            status="Starting",
            time_left="Unknown",
            transfer_rate="Unknown",
            date_added="Now",
        )

        stop_flag = threading.Event()
        self.app.download_stop_flags[item] = stop_flag

        thread = threading.Thread(
            target=self.download_file, args=(url, folder, item, stop_flag)
        )
        self.app.download_threads[item] = thread
        thread.start()

    def download_file(self, url, folder, item, stop_flag):
        """
        Handles the actual file download logic.
        """
        try:
            self.app.download_table.update_progress(item, progress="0%", status="Downloading")
            result = download_file(url, folder, stop_event=stop_flag, progress_callback=self.update_progress_callback)
            self.app.update_status(f"Download completed: {result}", "green")
            self.app.download_table.update_progress(item, progress="100%", status="Completed")

        except Exception as e:
            self.app.update_status(f"Download failed: {str(e)}", "red")
            self.app.download_table.update_progress(item, status="Error")

    def update_progress_callback(self, percent, eta, speed):
        """
        Updates the UI with download progress.
        """
        self.app.update_status(f"Progress: {percent}, ETA: {eta}, Speed: {speed}", "blue")

    def stop_download(self):
        """
        Stops the selected download.
        """
        try:
            selected_item = self.app.download_table.tree.focus()
            if not selected_item:
                raise ValueError("No download selected to stop.")

            self._stop_download(selected_item)

        except ValueError as ve:
            self.app.update_status(f"Error: {ve}", "red")
        except Exception as e:
            self.app.update_status(f"Unexpected Error: {str(e)}", "red")

    def stop_all_downloads(self):
        """
        Stops all ongoing downloads.
        """
        try:
            if not self.app.download_stop_flags:
                raise ValueError("No downloads are currently in progress.")

            for item in self.app.download_stop_flags:
                self._stop_download(item)

            self.app.update_status("All downloads stopped successfully.", "orange")

        except ValueError as ve:
            self.app.update_status(f"Error: {ve}", "red")
        except Exception as e:
            self.app.update_status(f"Unexpected Error: {str(e)}", "red")

    def _stop_download(self, item):
        """
        Stops a single download and updates the table.
        Args:
            item (str): The unique identifier of the download in the table.
        """
        if item in self.app.download_stop_flags:
            self.app.download_stop_flags[item].set()
            self.app.download_table.update_progress(item, status="Stopped", progress="0%")

    def delete_completed_downloads(self):
        """
        Deletes all completed downloads from the table.
        """
        try:
            items_to_delete = [
                item for item in self.app.download_table.tree.get_children()
                if self.app.download_table.tree.item(item, "values")[3] == "Completed"  # Assuming 'Status' is the 4th column
            ]

            if not items_to_delete:
                self.app.update_status("No completed downloads to delete.", "orange")
                return

            for item in items_to_delete:
                self.app.download_table.tree.delete(item)

            self.app.update_status("All completed downloads deleted successfully.", "green")

        except Exception as e:
            self.app.update_status(f"Unexpected Error: {str(e)}", "red")
