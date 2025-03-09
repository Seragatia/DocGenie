#gui/main_window.py
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox

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
from gui.utils.file_ops import save_download_info

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
        self.root.withdraw()  # Hide until we've applied the theme and created widgets

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

        # 3. Detect system theme (dark/light) and pick your theme dictionary
        self.theme_mode = self.detect_system_theme()
        self.theme = dark_theme if self.theme_mode == "dark" else light_theme

        # 4. Apply any global styles before creating widgets
        self.apply_custom_styles()

        # 5. Create main GUI components (menus, toolbars, tables, etc.)
        self.menu_bar = MenuBar(root, self)
        self.toolbar = Toolbar(root, self)
        self.download_table = DownloadTable(root, self)
        self.status_label = StatusLabel(root, self.theme)

        # 6. Apply the current theme to all components
        self.apply_theme()

        # 7. Initialize Clipboard Monitor
        self.clipboard_monitor = ClipboardMonitor(self)
        self.clipboard_monitor.start_monitoring()

        # Bind "Add URL" button to open dialog
        self.toolbar.add_url_button.config(command=self.show_add_url_window)

        # Ensure graceful shutdown
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # 8. Now that everything is styled and created, show the window
        self.root.update_idletasks()  # Force layout and theme updates
        self.root.deiconify()         # Reveal the main window
        self.root.lift()
        self.root.focus_force()

        logging.debug("DownloaderApp initialized successfully")

    def detect_system_theme(self) -> str:
        """Detects the system theme (dark or light)."""
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
        logging.debug("Toggling theme")
        self.theme_mode = "dark" if self.theme_mode != "dark" else "light"
        self.theme = dark_theme if self.theme_mode == "dark" else light_theme
        self.apply_custom_styles()
        self.apply_theme()

        # If AuthorizationDialog is open, refresh it too:
        if AuthorizationDialog._active_dialog:
            AuthorizationDialog._active_dialog.refresh_theme(self.theme)

        # If any DownloadOptionsDialog is open, refresh it:
        if DownloadOptionsDialog._active_dialog:
           DownloadOptionsDialog._active_dialog.refresh_theme(self.theme)

    def apply_theme(self) -> None:
        """Apply the current theme to all GUI components."""
        logging.debug("Applying theme")
        self.root.configure(bg=self.theme.get("bg", "#ffffff"))
        self.menu_bar.apply_theme(self.theme)
        self.toolbar.update_theme(self.theme)
        self.download_table.apply_theme(self.theme)
        self.status_label.apply_theme(self.theme)
        self.root.update_idletasks()

    def apply_custom_styles(self) -> None:
        """Configure global ttk styles for various widgets."""
        logging.debug("Applying custom styles")
        style = ttk.Style()
        style.theme_use("clam")

    def show_add_url_window(self, url: str = "") -> None:
        """Handles the sequence of dialogs to add a new URL."""
        logging.debug("Opening AuthorizationDialog")
        auth_dialog = AuthorizationDialog(self.root, url=url, theme=self.theme)
        # Wait until the AuthorizationDialog is closed
        self.root.wait_window(auth_dialog)
        auth_result = getattr(auth_dialog, "result", None)

        if auth_result is None:
            logging.warning("Authorization canceled")
            self.update_status("❌ Authorization canceled.", color="red")
            return

        validated_url = auth_result.get("url", "").strip()
        if not validate_url(validated_url):
            logging.warning("Invalid URL entered")
            messagebox.showwarning("Invalid URL", "⚠️ Please enter a valid URL.")
            return

        logging.debug(f"URL validated: {validated_url}")
        logging.debug("Opening DownloadOptionsDialog")
        download_dialog = DownloadOptionsDialog(self.root, url=validated_url, theme=self.theme)
        # Wait until the DownloadOptionsDialog is closed
        self.root.wait_window(download_dialog.dialog)
        download_result = getattr(download_dialog, "result", None)

        if download_result is None:
            logging.warning("Download canceled")
            self.update_status("⚠️ Download canceled.", color="orange")
            return

        logging.debug("Starting download")
        self.start_download(download_result)


    def start_download(self, download_info: dict) -> None:
        """Starts the download process."""
        logging.debug("Performing download process")
        self._perform_download(download_info)

    def _perform_download(self, download_info: dict) -> None:
        """Simulates a download process."""
        url = download_info["url"]
        save_path = download_info["save_path"]
        logging.info(f"Downloading: {save_path}")
        self.update_status(f"📥 Downloading: {save_path}...", color="blue")
        import time
        time.sleep(5)
        save_download_info(download_info)
        self.download_table.mark_completed(url)
        self.update_status(f"✅ Download completed: {save_path}", color="green")

    def update_status(self, message: str, color: str = "black") -> None:
        """Update the status label with a given message."""
        logging.debug(f"Status updated: {message}")
        self.status_label.update_status(message, color)

    def on_exit(self) -> None:
        """Handles application exit, ensuring clipboard monitoring stops."""
        logging.debug("Exiting application")
        self.clipboard_monitor.stop_monitoring()
        self.root.quit()

if __name__ == "__main__":
    logging.info("Starting DownloaderApp")
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()
