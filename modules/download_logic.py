import threading

class DownloadLogic:
    def __init__(self, app):
        self.app = app  # Store reference to the main app

    def start_download(self):
        """Handles starting a new download."""
        self.app.update_status("Starting download...", "green")
        url = self.app.url_input.get_url()
        folder = self.app.url_input.get_output_folder()

        if not url or not folder:
            self.app.update_status("Error: URL and folder are required!", "red")
            return

        item = self.app.download_table.add_row(url)
        self.app.update_status("Downloading...", "green")

        stop_flag = threading.Event()
        self.app.download_stop_flags[item] = stop_flag
        thread = threading.Thread(target=self.download_file, args=(url, folder, item, stop_flag))
        self.app.download_threads[item] = thread
        thread.start()

    def resume_download(self):
        """Handles resuming paused downloads."""
        self.app.update_status("Resume functionality not implemented yet.", "orange")

    def stop_download(self):
        """Stops the selected download."""
        self.app.update_status("Stop functionality not implemented yet.", "orange")

    def stop_all_downloads(self):
        """Stops all ongoing downloads."""
        self.app.update_status("Stop All functionality not implemented yet.", "orange")

    def delete_selected(self):
        """Deletes the selected downloads."""
        self.app.update_status("Delete functionality not implemented yet.", "orange")

    def delete_completed_downloads(self):
        """Deletes all completed downloads."""
        for item in self.app.download_table.tree.get_children():
            status = self.app.download_table.tree.item(item, "values")[3]  # Assuming status is in column 3
            if status == "Completed":
                self.app.download_table.tree.delete(item)
        self.app.update_status("All completed downloads deleted.", "blue")
