#gui/download_table.py
import tkinter as tk
from tkinter import ttk
from themes import dark_theme, light_theme
import json  # For storing column widths persistently
from typing import Any, Optional


class DownloadTable:
    """
    A table widget (using ttk.Treeview) for displaying download information.
    Each row represents one download. Columns include:
    ['File Name', 'Size', 'Progress', 'Status', 'Time Left',
     'Transfer Rate', 'Date Added', 'File Type', 'Resolution',
     'Download Path', 'Source URL'].
    """

    def __init__(self, root: tk.Widget, parent_app: Any) -> None:
        """
        Initializes the download table without duplication.
        :param root: The Tkinter parent widget (frame or window).
        :param parent_app: Reference to the main app or window object.
        """
        self.parent_app = parent_app
        self.columns = [
            "File Name",
            "Size",
            "Progress",
            "Status",
            "Time Left",
            "Transfer Rate",
            "Date Added",
            "File Type",
            "Resolution",
            "Download Path",
            "Source URL",
        ]

        # Prevent duplicate tables
        if hasattr(self.parent_app, "download_table"):
            print("⚠️ Warning: DownloadTable already exists. Reusing existing instance.")
            self.parent_app.download_table = self
            return

        self.parent_app.download_table = self  # Register table instance in the app

        # Main Table Frame
        self.table_frame = ttk.Frame(root)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbars for the table
        self.scroll_y = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, style="Vertical.TScrollbar")
        self.scroll_x = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL, style="Horizontal.TScrollbar")

        # Treeview for displaying downloads
        self.tree = ttk.Treeview(
            self.table_frame,
            columns=self.columns,
            show="headings",
            selectmode="extended",
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self.scroll_x.set,
        )
        self.scroll_y.config(command=self.tree.yview)
        self.scroll_x.config(command=self.tree.xview)

        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Configure Columns with default width settings
        for col in self.columns:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=150, minwidth=100, stretch=True)

        # Load persisted column widths if available
        self.load_column_widths()

        # Apply the current theme from parent app
        self.apply_theme(self.parent_app.theme)

        # Configure tags for dark/light mode appearances
        self.tree.tag_configure("dark", background=dark_theme.get("table_bg"), foreground=dark_theme.get("fg"))
        self.tree.tag_configure("light", background="white", foreground="black")

        # Dictionary to store progress bars per row
        self.progress_bars = {}

    def apply_theme(self, theme: dict) -> None:
        """
        Apply the selected theme dynamically, including scrollbar styling.
        :param theme: A dictionary containing theme settings.
        """
        style = ttk.Style()

        # Table styling
        style.configure(
            "Treeview",
            background=theme.get("table_bg", "white"),
            foreground=theme.get("fg", "black"),
            fieldbackground=theme.get("table_bg", "white"),
            font=("Arial", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=theme.get("toolbar_bg", "#f0f0f0"),
            foreground=theme.get("fg", "black"),
            font=("Arial", 11, "bold"),
            padding=(8, 5),
        )

        # Scrollbar styling
        scrollbar_bg = theme.get("scrollbar_bg", "#E0E0E0")
        scrollbar_trough = theme.get("scrollbar_trough", "#808080")
        scrollbar_thumb = theme.get("scrollbar_thumb", "#C0C0C0")
        scrollbar_arrow = theme.get("scrollbar_arrow", "#606060")

        style.configure("Vertical.TScrollbar",
                        background=scrollbar_bg,
                        troughcolor=scrollbar_trough,
                        arrowcolor=scrollbar_arrow,
                        borderwidth=2)
        style.configure("Horizontal.TScrollbar",
                        background=scrollbar_bg,
                        troughcolor=scrollbar_trough,
                        arrowcolor=scrollbar_arrow,
                        borderwidth=2)

        # Improve scrollbar thumb visibility
        style.map("Vertical.TScrollbar",
                  background=[("active", scrollbar_thumb)],
                  relief=[("pressed", "sunken")])
        style.map("Horizontal.TScrollbar",
                  background=[("active", scrollbar_thumb)],
                  relief=[("pressed", "sunken")])

        # Refresh the treeview appearance
        self.tree.update_idletasks()

    def load_column_widths(self, filename: str = "column_widths.json") -> None:
        """
        Load persisted column widths from a JSON file and apply them.
        """
        try:
            with open(filename, "r") as f:
                widths = json.load(f)
            for col in self.columns:
                if col in widths:
                    self.tree.column(col, width=widths[col])
        except FileNotFoundError:
            pass  # No persisted settings found; use default widths.
        except json.JSONDecodeError:
            print("⚠️ Error decoding column widths file. Using default widths.")

    def save_column_widths(self, filename: str = "column_widths.json") -> None:
        """
        Save current column widths to a JSON file for persistence.
        """
        widths = {col: self.tree.column(col)["width"] for col in self.columns}
        try:
            with open(filename, "w") as f:
                json.dump(widths, f)
            print("✅ Column widths saved successfully.")
        except Exception as e:
            print(f"⚠️ Error saving column widths: {e}")

    def update_progress(self, url: str, progress: int) -> None:
        """
        Updates the progress bar for a specific download in the table.
        
        :param url: The source URL of the download.
        :param progress: The current progress percentage (0-100).
        """
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values and values[-1] == url:  # Check if the last column (Source URL) matches
                self.tree.set(item, "Progress", f"{progress}%")
                self.tree.set(item, "Status", "Downloading..." if progress < 100 else "Completed")
                self.tree.update_idletasks()
                return
        print(f"⚠️ Warning: No matching download found for URL: {url}")

    def mark_completed(self, url: str) -> None:
        """
        Marks a download as completed in the table.
        
        :param url: The source URL of the completed download.
        """
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values and values[-1] == url:
                self.tree.set(item, "Progress", "100%")
                self.tree.set(item, "Status", "Completed")
                self.tree.update_idletasks()
                return
        print(f"⚠️ Warning: No matching download found to mark as completed: {url}")
