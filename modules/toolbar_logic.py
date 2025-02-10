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
        self.app.show_add_url_window()

    def resume_download(self):
        """Handles resuming a download."""
        self.app.download_logic.resume_download()

    def stop_download(self):
        """Handles stopping a download."""
        self.app.download_logic.stop_download()

    def stop_all_downloads(self):
        """Handles stopping all downloads."""
        self.app.download_logic.stop_all_downloads()

    def delete_selected(self):
        """Handles deleting the selected download."""
        self.app.download_logic.delete_selected()
