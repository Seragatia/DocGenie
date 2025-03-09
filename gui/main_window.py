# gui/main_window.py
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

# GUI Modules
from gui.toolbar import Toolbar
from gui.download_table import DownloadTable
from gui.menu_bar import MenuBar
from gui.status_label import StatusLabel
from gui.dialogs.auth_dialog import AuthorizationDialog
from gui.dialogs.download_dialog import DownloadOptionsDialog
from gui.clipboard_monitor import ClipboardMonitor

# Utility Modules
from gui.utils.helpers import validate_url
# Instead of old code, we call the real backend
from gui.utils.api_requests import (
    start_download as api_start_download,
    get_download_status,
    list_downloads,
    pause_download,
    resume_download,
    cancel_download,
)

# Theme dictionaries
from themes import dark_theme, light_theme

# Enable logging for debugging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

class DownloaderApp:
    """Main application class for the Advanced Downloader."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the main downloader application window."""
        logging.debug("Initializing DownloaderApp")

        # 1. Hide the main window until fully styled
        self.root = root
        self.root.withdraw()

        self.root.title("Advanced Downloader")
        self.root.geometry("1024x600")
        self.root.minsize(800, 500)
        self.root.resizable(True, True)

        # Prevent multiple instances
        if hasattr(self.root, "_app_instance"):
            logging.warning("DownloaderApp instance already exists.")
            return
        self.root._app_instance = True

        # 2. Force the "clam" theme globally, so all widgets pick up custom styling
        style = ttk.Style()
        style.theme_use("clam")

        # 3. Detect system theme and pick a theme dictionary
        self.theme_mode = self.detect_system_theme()
        self.theme = dark_theme if self.theme_mode == "dark" else light_theme

        # 4. Apply any global styles before creating widgets
        self.apply_custom_styles()

        # 5. Create main GUI components
        self.menu_bar = MenuBar(root, self)
        self.toolbar = Toolbar(root, self)
        self.download_table = DownloadTable(root, self)
        self.status_label = StatusLabel(root, self.theme)

        # 6. Apply the current theme
        self.apply_theme()

        # 7. Initialize Clipboard Monitor
        self.clipboard_monitor = ClipboardMonitor(self)
        self.clipboard_monitor.start_monitoring()

        # Bind "Add URL" button to open dialog
        self.toolbar.add_url_button.config(command=self.show_add_url_window)

        # Ensure graceful shutdown
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # 8. Show the window after styling is applied
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

        logging.debug("DownloaderApp initialized successfully")

    def detect_system_theme(self) -> str:
        """Detect the system theme (dark or light) based on platform."""
        logging.debug("Detecting system theme")
        if sys.platform == "win32":
            import ctypes
            try:
                is_dark = ctypes.windll.uxtheme.ShouldAppsUseDarkMode() == 1
                return "dark" if is_dark else "light"
            except AttributeError:
                return "light"
        elif sys.platform == "darwin":
            from subprocess import run
            result = run(["defaults", "read", "-g", "AppleInterfaceStyle"], capture_output=True, text=True)
            return "dark" if "Dark" in result.stdout else "light"
        else:
            try:
                from gi.repository import Gio
                theme = Gio.Settings.new("org.gnome.desktop.interface").get_string("color-scheme")
                return "dark" if "dark" in theme.lower() else "light"
            except Exception:
                return "light"

    def toggle_theme(self) -> None:
        """Toggle between dark and light themes and reapply settings."""
        logging.debug("Toggling theme.")
        self.theme_mode = "dark" if self.theme_mode != "dark" else "light"
        self.theme = dark_theme if self.theme_mode == "dark" else light_theme
        self.apply_custom_styles()
        self.apply_theme()

        # Refresh theme in any open dialogs
        if AuthorizationDialog._active_dialog:
            AuthorizationDialog._active_dialog.refresh_theme(self.theme)
        if DownloadOptionsDialog._active_dialog:
            DownloadOptionsDialog._active_dialog.refresh_theme(self.theme)

    def apply_theme(self) -> None:
        """Apply the current theme to all GUI components."""
        logging.debug("Applying current theme to the application.")
        self.root.configure(bg=self.theme.get("bg", "#ffffff"))
        self.menu_bar.apply_theme(self.theme)
        self.toolbar.update_theme(self.theme)
        self.download_table.apply_theme(self.theme)
        self.status_label.apply_theme(self.theme)
        self.root.update_idletasks()

    def apply_custom_styles(self) -> None:
        """Configure global ttk styles for various widgets."""
        logging.debug("Applying custom global ttk styles.")
        style = ttk.Style()
        style.theme_use("clam")
        # Add any global style overrides here

    def show_add_url_window(self, url: str = "") -> None:
        """Open the authorization dialog, then the download dialog."""
        logging.debug("Opening AuthorizationDialog")
        auth_dialog = AuthorizationDialog(self.root, url=url, theme=self.theme)
        self.root.wait_window(auth_dialog)
        auth_result = getattr(auth_dialog, "result", None)

        if auth_result is None:
            logging.warning("Authorization canceled by user.")
            self.update_status("❌ Authorization canceled.", color="red")
            return

        validated_url = auth_result.get("url", "").strip()
        if not validate_url(validated_url):
            logging.warning("Invalid URL entered.")
            messagebox.showwarning("Invalid URL", "⚠️ Please enter a valid URL.")
            return

        logging.debug(f"URL validated: {validated_url}")
        logging.debug("Opening DownloadOptionsDialog")
        download_dialog = DownloadOptionsDialog(self.root, url=validated_url, theme=self.theme)
        self.root.wait_window(download_dialog.dialog)
        download_result = getattr(download_dialog, "result", None)

        if download_result is None:
            logging.warning("Download canceled by user.")
            self.update_status("⚠️ Download canceled.", color="orange")
            return

        logging.debug("Starting download process.")
        self.start_download(download_result)

    def start_download(self, download_info: dict) -> None:
        """
        Offloads the entire download process to a background thread.
        Instead of simulating, we'll call the Rust backend:
          1) start_download() with the specified info
          2) poll get_download_status() every second
          3) update the UI with progress
        """
        logging.debug("Preparing to download in a separate thread.")

        def download_task():
            """Thread function that calls the backend, then polls for progress."""
            url = download_info["url"]
            save_path = download_info["save_path"]
            segments = 1
            if "action" in download_info and download_info["action"] == "start_now":
                # If the user or dialog indicates we can do multi-thread:
                # Or we can parse from dialog if we want to do segmented
                segments = 1 # or parse from download_info if it has "segments"
            
            # Build request data for the backend
            request_data = {
                "id": "",  # let the backend assign if empty
                "url": url,
                "destination": save_path,
                "status": "pending",
                "progress": 0.0,
                "segments": segments
            }

            self.root.after(0, lambda: self.update_status(f"📥 Starting download for: {save_path}", "blue"))

            # 1) Call the backend to start the download
            start_resp = api_start_download(request_data)
            if "error" in start_resp:
                # Show an error in the UI
                err_msg = start_resp["error"]
                logging.error(f"Failed to start download: {err_msg}")
                self.root.after(0, lambda: self.update_status(f"❌ Error: {err_msg}", "red"))
                return

            task_id = start_resp.get("task_id", "")
            if not task_id:
                logging.error("No task_id returned from backend.")
                self.root.after(0, lambda: self.update_status("❌ Error: No task_id from backend", "red"))
                return

            # 2) Poll get_download_status() every second
            while True:
                st = get_download_status(task_id)
                if "error" in st:
                    err_msg = st["error"]
                    logging.error(f"Polling error for task {task_id}: {err_msg}")
                    self.root.after(0, lambda: self.update_status(f"❌ Error: {err_msg}", "red"))
                    break

                status = st.get("status", "unknown")
                progress = st.get("progress", 0.0)
                # Update the UI with the current progress
                self.root.after(0, lambda s=status, p=progress: self.update_status(
                    f"Download {task_id}: {s} - {p:.1f}% complete", "blue"
                ))
                # If it's completed or failed, break
                if status in ["completed", "failed"]:
                    # Mark the table if we consider it "done"
                    if status == "completed":
                        self.root.after(0, lambda: self.download_table.mark_completed(url))
                        self.root.after(0, lambda: self.update_status(f"✅ Download completed: {save_path}", color="green"))
                    else:
                        self.root.after(0, lambda: self.update_status(f"❌ Download failed: {save_path}", color="red"))
                    break

                time.sleep(1)

        # Run the entire logic in a daemon thread so the UI remains responsive
        threading.Thread(target=download_task, daemon=True).start()

    def update_status(self, message: str, color: str = "black") -> None:
        """Update the status label with a given message."""
        logging.debug(f"Status updated: {message}")
        self.status_label.update_status(message, color)

    def on_exit(self) -> None:
        """Cleanly exit the application by stopping the clipboard monitor."""
        logging.debug("Exiting application.")
        self.clipboard_monitor.stop_monitoring()
        self.root.quit()

if __name__ == "__main__":
    logging.info("Starting DownloaderApp.")
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()
