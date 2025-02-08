import tkinter as tk
from tkinter import ttk
from gui.table_utils import make_table_scrollable

class DownloadTable:
    def __init__(self, root):
        """
        Initializes the download table with dynamic columns and proper scrolling.
        Args:
            root (tk.Tk or tk.Frame): The parent Tkinter container.
        """
        self.columns = [
            "File Name", "Size", "Progress", "Status", "Time Left",
            "Transfer Rate", "Date Added", "File Type", "Resolution",
            "Download Path", "Source URL"
        ]  # Supports an extended number of columns

        self.table_frame = tk.Frame(root)
        self.table_frame.pack(pady=10, fill=tk.BOTH, expand=True)

        # Scrollable Canvas (For Large Tables)
        self.canvas = tk.Canvas(self.table_frame)
        self.inner_frame = tk.Frame(self.canvas)  # Frame inside Canvas for proper scrolling

        # Scrollbars
        self.scrollbar_y = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        # Packing Scrollbars
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview (Table)
        self.tree = ttk.Treeview(
            self.inner_frame,
            columns=self.columns,
            show="headings",
            height=10,
        )

        # Define Columns
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=180, minwidth=150, stretch=True)  # Adjustable for long tables

        # Packing Treeview
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Attach frame to canvas
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Enable scrolling dynamically
        make_table_scrollable(self.canvas, self.inner_frame)

    def add_row(self, **kwargs):
        """
        Adds a new row to the table dynamically.
        Args:
            kwargs (dict): Dictionary of column values.
        Returns:
            str: The unique identifier of the added row.
        """
        row_values = [kwargs.get(col, "N/A") for col in self.columns]
        return self.tree.insert("", "end", values=row_values)

    def update_row(self, item, **kwargs):
        """
        Updates a specific row in the table.
        Args:
            item (str): The unique identifier of the row.
            kwargs (dict): Updated values, e.g., progress="50%", status="Downloading".
        """
        current_values = list(self.tree.item(item, "values"))

        for key, value in kwargs.items():
            if key in self.columns:
                col_index = self.columns.index(key)
                current_values[col_index] = value

        self.tree.item(item, values=current_values)

    def delete_row(self, item):
        """
        Deletes a row from the table.
        Args:
            item (str): The unique identifier of the row to delete.
        """
        self.tree.delete(item)

    def clear_table(self):
        """
        Clears all rows in the table.
        """
        for item in self.tree.get_children():
            self.tree.delete(item)
