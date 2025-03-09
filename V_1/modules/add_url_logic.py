# add_url_logic.py
import os
import re
import time
import logging
from tkinter import Toplevel, StringVar, filedialog, ttk

# ✅ Set up logging
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class AddURLLogic:
    """
    Handles user input for adding a download URL and download details.
    """

    def __init__(self, app):
        """
        Args:
            app: Reference to the main application instance.
        """
        self.app = app
        self.download_url = ""  # ✅ Store URL for persistence

    def process_url(self, window, url, use_auth, login, password):
        """
        Processes the URL input and opens the download details window.
        """
        try:
            if not url.strip():
                self.app.status_label.update_status("Error: URL is required!", "red")
                return

            if use_auth and (not login.strip() or not password.strip()):
                self.app.status_label.update_status(
                    "Error: Login and password are required.", "red"
                )
                return

            # ✅ Store URL in instance variable before passing
            self.download_url = url.strip()

            # ✅ Open the Download File Info dialog
            self.show_download_file_info(url)

            # ✅ Close the Add URL window
            window.destroy()

        except Exception as e:
            logging.error(f"URL Processing Error: {e}")
            self.app.status_label.update_status(f"Unexpected error: {e}", "red")

    def show_download_file_info(self, url):
        """
        Displays the "Download File Info" dialog.
        """
        dialog = Toplevel(self.app.root)
        dialog.title("Download File Info")
        dialog.geometry("500x350")
        dialog.resizable(False, False)

        # ✅ Apply Theme
        theme = self.app.theme
        dialog.configure(bg=theme["bg"])

        # ✅ Extract a valid filename
        clean_filename = self.extract_valid_filename(url)
        file_path_var = StringVar(value=os.path.join("Downloads", clean_filename))

        # ✅ Variables
        category_var = StringVar(value="General")
        description_var = StringVar()

        # ✅ Use ttk.Frame for better layout
        form_frame = ttk.Frame(dialog, padding=(10, 10))
        form_frame.pack(fill="both", expand=True)

        # ✅ Labels and Inputs
        ttk.Label(form_frame, text="URL:").grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        ttk.Entry(
            form_frame, state="readonly", textvariable=StringVar(value=url), width=60
        ).grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(form_frame, text="Category:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        category_menu = ttk.Combobox(
            form_frame,
            textvariable=category_var,
            values=["General", "Videos", "Documents", "Music", "Other"],
            state="readonly",
        )
        category_menu.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(form_frame, text="Save As:").grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )
        ttk.Entry(form_frame, textvariable=file_path_var, width=50).grid(
            row=2, column=1, padx=10, pady=5, sticky="w"
        )
        ttk.Button(
            form_frame, text="...", command=lambda: self.select_file(file_path_var)
        ).grid(row=2, column=2, padx=5, pady=5)

        ttk.Label(form_frame, text="Description:").grid(
            row=3, column=0, padx=10, pady=5, sticky="w"
        )
        ttk.Entry(form_frame, textvariable=description_var, width=60).grid(
            row=3, column=1, padx=10, pady=5
        )

        # ✅ Button Alignment Fix
        button_frame = ttk.Frame(dialog, padding=(10, 10))
        button_frame.pack(fill="x")

        ttk.Button(button_frame, text="Download Later", command=dialog.destroy).pack(
            side="right", padx=5
        )
        ttk.Button(
            button_frame,
            text="Start Download",
            command=lambda: self.start_download_with_details(
                url,
                file_path_var.get(),
                category_var.get(),
                description_var.get(),
                dialog,
            ),
        ).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(
            side="right", padx=5
        )

    def extract_valid_filename(self, url):
        """
        Extracts a valid filename from a URL and ensures a proper file extension.
        """
        filename = (
            os.path.basename(url).split("?")[0].strip()
        )  # ✅ Remove query parameters & trim spaces

        # ✅ Generate a random name if filename is missing
        if not filename or "." not in filename:
            filename = f"download_{int(time.time())}.mp4"

        # ✅ Replace invalid characters with underscores
        filename = re.sub(r"[^\w\-_\. ]", "_", filename)

        # ✅ Ensure a valid file extension
        valid_extensions = (".mp4", ".mp3", ".pdf", ".zip", ".txt")
        if not filename.endswith(valid_extensions):
            filename += ".mp4"  # Default to MP4 if no extension

        return filename

    def start_download_with_details(
        self, url, file_path, category, description, dialog
    ):
        """
        Starts a download with detailed information.
        """
        try:
            if not url.strip() or not file_path.strip():
                raise ValueError("URL and file path are required.")

            # ✅ Ensure the download directory exists
            save_dir = os.path.dirname(file_path)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)  # ✅ Create the directory if it doesn't exist

            # ✅ Add the download to the table and store the row ID
            item_id = self.app.download_table.add_row(
                file_name=os.path.basename(file_path),
                size="Calculating...",
                progress="0%",
                status="Starting",
                time_left="Unknown",
                transfer_rate="Unknown",
                date_added="Now",
            )

            # ✅ Refresh UI to reflect the new row
            self.app.download_table.tree.update_idletasks()

            # ✅ Start the actual download process
            self.app.download_logic._add_and_start_download(
                url, save_dir, file_path, category, description
            )

            # ✅ Update UI status
            self.app.status_label.update_status(f"Started downloading: {url}", "green")

            # ✅ Enable "Start Download" button if at least one entry exists
            self.app.toolbar.enable_start_button()

            # ✅ Close the dialog
            dialog.destroy()

        except Exception as e:
            logging.error(f"Download Error: {e}")  # ✅ Log the error in app.log
            self.app.status_label.update_status(f"Unexpected Error: {e}", "red")

    def select_file(self, file_path_var):
        """
        Opens a file dialog to select a save-as path with appropriate file extensions.
        """
        file_types = [
            ("MP4 Video", "*.mp4"),
            ("MP3 Audio", "*.mp3"),
            ("PDF Document", "*.pdf"),
            ("ZIP Archive", "*.zip"),
            ("Text File", "*.txt"),
            ("All Files", "*.*"),
        ]

        file_path = filedialog.asksaveasfilename(
            defaultextension=".mp4", filetypes=file_types
        )
        if file_path:
            file_path_var.set(file_path)
