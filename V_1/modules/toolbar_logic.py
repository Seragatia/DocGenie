import logging

# ✅ Set up logging
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class ToolbarLogic:
    def __init__(self, app):
        """
        Initializes the ToolbarLogic class.

        Args:
            app: Reference to the main application instance.
        """
        self.app = app

    def add_url(self):
        """Handles the Add URL button click."""
        try:
            self.app.show_add_url_window()
        except Exception as e:
            logging.error(f"Error opening Add URL window: {e}")
            self.app.status_label.update_status(
                "Error: Could not open Add URL window.", "red"
            )

    def start_download(self):
        """Handles starting a download."""
        try:
            selected = self.app.download_table.get_selected_download()
            if not selected:
                self.app.status_label.update_status(
                    "Error: No download selected.", "red"
                )
                return

            self.app.download_logic.start_download(selected)
            self.update_button_states()
        except Exception as e:
            logging.error(f"Error starting download: {e}")
            self.app.status_label.update_status(
                "Error: Could not start download.", "red"
            )

    def resume_download(self):
        """Handles resuming a paused download."""
        try:
            selected = self.app.download_table.get_selected_download()
            if not selected:
                self.app.status_label.update_status(
                    "Error: No download selected.", "red"
                )
                return

            self.app.download_logic.resume_download(selected)
            self.update_button_states()
        except Exception as e:
            logging.error(f"Error resuming download: {e}")
            self.app.status_label.update_status(
                "Error: Could not resume download.", "red"
            )

    def stop_download(self):
        """Handles stopping a download."""
        try:
            selected = self.app.download_table.get_selected_download()
            if not selected:
                self.app.status_label.update_status(
                    "Error: No download selected.", "red"
                )
                return

            self.app.download_logic.stop_download(selected)
            self.update_button_states()
        except Exception as e:
            logging.error(f"Error stopping download: {e}")
            self.app.status_label.update_status(
                "Error: Could not stop download.", "red"
            )

    def stop_all_downloads(self):
        """Handles stopping all downloads."""
        try:
            if not self.app.download_table.has_active_downloads():
                self.app.status_label.update_status(
                    "Error: No active downloads to stop.", "red"
                )
                return

            self.app.download_logic.stop_all_downloads()
            self.update_button_states()
        except Exception as e:
            logging.error(f"Error stopping all downloads: {e}")
            self.app.status_label.update_status(
                "Error: Could not stop all downloads.", "red"
            )

    def delete_selected(self):
        """Handles deleting the selected download."""
        try:
            selected = self.app.download_table.get_selected_download()
            if not selected:
                self.app.status_label.update_status(
                    "Error: No download selected.", "red"
                )
                return

            self.app.download_logic.delete_selected(selected)
            self.update_button_states()
        except Exception as e:
            logging.error(f"Error deleting download: {e}")
            self.app.status_label.update_status(
                "Error: Could not delete download.", "red"
            )

    def update_button_states(self):
        """✅ Enables or disables toolbar buttons based on download state."""
        has_downloads = self.app.download_table.has_downloads()
        has_active_downloads = self.app.download_table.has_active_downloads()
        selected = self.app.download_table.get_selected_download()

        # ✅ Enable/Disable buttons dynamically
        self.app.toolbar.start_button.config(state="normal" if selected else "disabled")
        self.app.toolbar.stop_button.config(
            state="normal" if has_active_downloads else "disabled"
        )
        self.app.toolbar.delete_button.config(
            state="normal" if selected else "disabled"
        )

        # ✅ Update "Stop All" button based on active downloads
        self.app.toolbar.stop_all_button.config(
            state="normal" if has_active_downloads else "disabled"
        )
