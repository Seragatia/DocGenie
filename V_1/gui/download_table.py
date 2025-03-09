import tkinter as tk
from tkinter import ttk
from themes import dark_theme, light_theme
import json  # ✅ Store column widths persistently


class DownloadTable:
    def __init__(self, root, parent_app):
        """
        ✅ Initializes the download table properly without duplication.
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

        # ✅ Prevent duplicate tables
        if hasattr(self.parent_app, "download_table"):
            print("⚠️ Warning: DownloadTable already exists. Reusing existing instance.")
            self.parent_app.download_table = self
            return

        self.parent_app.download_table = self  # ✅ Register table instance in the app

        # ✅ Main Table Frame (Now dynamically resizable)
        self.table_frame = ttk.Frame(root)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ✅ Scrollbars
        self.scroll_y = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL)
        self.scroll_x = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL)

        # ✅ Treeview for Displaying Downloads
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

        # ✅ Configure Columns Correctly
        for col in self.columns:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, width=150, minwidth=100, stretch=True)

        # ✅ Apply Theme Properly
        self.apply_theme(self.parent_app.theme)

        # ✅ Prevent table duplication in dark mode
        self.tree.tag_configure(
            "dark", background=dark_theme["table_bg"], foreground=dark_theme["fg"]
        )
        self.tree.tag_configure("light", background="white", foreground="black")

    def apply_theme(self, theme):
        """✅ Apply the selected theme dynamically to avoid duplication issues."""
        style = ttk.Style()

        # ✅ Table Background Styling
        style.configure(
            "Treeview",
            background=theme["table_bg"],
            foreground=theme["fg"],
            fieldbackground=theme["table_bg"],
            font=("Arial", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=theme["toolbar_bg"],
            foreground=theme["fg"],
            font=("Arial", 11, "bold"),
            padding=(8, 5),
        )

        # ✅ Fix Scrollbars for Dark Mode
        style.configure(
            "Vertical.TScrollbar",
            troughcolor=theme["bg"],
            background=theme["toolbar_bg"],
            borderwidth=2,
        )
        style.configure(
            "Horizontal.TScrollbar",
            troughcolor=theme["bg"],
            background=theme["toolbar_bg"],
            borderwidth=2,
        )

        # ✅ Refresh Table Appearance
        self.tree.update_idletasks()

    def add_row(
        self,
        file_name,
        size,
        progress,
        status,
        time_left,
        transfer_rate,
        date_added,
        file_type="",
        resolution="",
        download_path="",
        source_url="",
    ):
        """
        ✅ Adds a new row to the table and returns the item ID.
        """
        existing_files = [
            self.tree.item(item, "values")[0] for item in self.tree.get_children()
        ]
        if file_name in existing_files:
            print(f"⚠️ Duplicate entry detected: {file_name}. Skipping table addition.")
            return None  # Prevent duplicate downloads in the UI

        item_id = self.tree.insert(
            "",
            "end",
            values=(
                file_name,
                size,
                progress,
                status,
                time_left,
                transfer_rate,
                date_added,
                file_type,
                resolution,
                download_path,
                source_url,
            ),
        )
        self.tree.update_idletasks()
        return item_id

    def update_progress(
        self, item_id, progress=None, status=None, time_left=None, transfer_rate=None
    ):
        """
        ✅ Updates the download progress in the table.
        """
        if not self.tree.exists(item_id):
            print(f"⚠️ Error: Item ID {item_id} not found in table!")
            return

        current_values = list(self.tree.item(item_id, "values"))

        # ✅ Preserve existing values if parameters are None
        if progress is not None:
            current_values[2] = progress  # Progress column index
        if status is not None:
            current_values[3] = status  # Status column index
        if time_left is not None:
            current_values[4] = time_left  # Time Left column index
        if transfer_rate is not None:
            current_values[5] = transfer_rate  # Transfer Rate column index

        self.tree.item(item_id, values=current_values)
        self.tree.update_idletasks()

    def delete_completed_downloads(self):
        """
        ✅ Removes all completed downloads from the table.
        """
        completed_items = [
            item
            for item in self.tree.get_children()
            if self.tree.item(item, "values")[3] == "Completed"
        ]

        if not completed_items:
            print("⚠️ No completed downloads to delete.")
            return

        for item in completed_items:
            self.tree.delete(item)

        print("✅ Completed downloads removed successfully.")
