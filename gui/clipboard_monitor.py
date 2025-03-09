"""
Clipboard Monitor for Automatic URL Detection

- Continuously monitors the clipboard for changes.
- If a valid URL is detected, it prompts the user with a popup.
- If the user confirms, it automatically opens the "Add URL" window.
- Runs as a background thread in the main GUI application.

Dependencies:
- pyperclip for clipboard access.
- tkinter for the popup.
- threading for background monitoring.
"""

import time
import pyperclip
import threading
import tkinter as tk
from tkinter import messagebox
from urllib.parse import urlparse
import logging

class ClipboardMonitor:
    """
    Monitors the clipboard for URL changes.
    If a valid URL is detected, prompts the user to add it for download.
    """

    def __init__(self, app, check_interval: float = 2.0) -> None:
        """
        Initializes the clipboard monitor.

        Args:
            app: The main GUI application instance (DownloaderApp).
            check_interval (float): How often to check the clipboard (in seconds).
        """
        self.app = app
        self.check_interval = check_interval
        self.last_clipboard = ""
        self.monitoring = False
        self.thread = None
        self.logger = logging.getLogger(__name__)

    def start_monitoring(self) -> None:
        """Starts the clipboard monitoring thread."""
        if not self.monitoring:
            self.monitoring = True
            self.thread = threading.Thread(target=self._monitor_clipboard, daemon=True)
            self.thread.start()
            self.logger.debug("Clipboard monitoring started.")

    def stop_monitoring(self) -> None:
        """Stops the clipboard monitoring thread."""
        self.monitoring = False
        self.logger.debug("Clipboard monitoring stopped.")

    def _monitor_clipboard(self) -> None:
        """Continuously checks the clipboard for new valid URLs."""
        while self.monitoring:
            time.sleep(self.check_interval)  # Prevent excessive CPU usage
            try:
                clipboard_content = pyperclip.paste().strip()
            except Exception as e:
                self.logger.error(f"Clipboard Error: {e}")
                continue

            # If a new valid URL is found, prompt the user (once)
            if clipboard_content and clipboard_content != self.last_clipboard and self._is_valid_url(clipboard_content):
                self.last_clipboard = clipboard_content  # Update last clipboard value
                # Schedule the popup in the main thread
                self.app.root.after(0, self._prompt_user, clipboard_content)

    def _is_valid_url(self, url: str) -> bool:
        """Returns True if the provided string is a valid URL."""
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    def _prompt_user(self, url: str) -> None:
        """
        Displays a confirmation popup for the detected URL.
        If confirmed, it calls the main window's show_add_url_window(url).
        """
        response = messagebox.askyesno(
            "New URL Detected",
            f"A new URL was copied:\n\n{url}\n\nWould you like to add this for download?"
        )
        if response:
            self.app.root.after(0, self.app.show_add_url_window, url)
