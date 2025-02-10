import tkinter as tk
from tkinter import ttk
from gui.table_utils import make_table_scrollable


class DownloadTable:
    def __init__(self, root):
        """
        Initializes the download table with dynamic columns, custom styling, and proper scrolling.
        Args:
            root (tk.Tk or tk.Frame): The parent Tkinter container.
        """
        self.columns = [
            "File Name", "Size", "Progress", "Status", "Time Left",
            "Transfer Rate", "Date Added", "File Type", "Resolution",
            "Download Path", "Source URL"
        ]

        # Styling the Treeview
        style = ttk.Style()
        style.configure(
            "Treeview",
            font=("Arial", 10),  # Font for rows
            rowheight=25,  # Height of rows
            background="#f8f9fa",  # Default background
            fieldbackground="#f8f9fa",  # Field background
            foreground="#212529",  # Text color
        )
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"), foreground="#495057")  # Header styling
        style.map("Treeview", background=[("selected", "#d1ecf1")])  # Highlight selected row

        self.table_frame = tk.Frame(root, bg="#ffffff", relief=tk.GROOVE, bd=2)
        self.table_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Canvas for scrolling
        self.canvas = tk.Canvas(self.table_frame, bg="#ffffff")
        self.tree_frame = tk.Frame(self.canvas, bg="#ffffff")  # Inner frame for the Treeview

        # Scrollbars
        self.scrollbar_y = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_x = ttk.Scrollbar(self.table_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        # Packing canvas and scrollbars
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Attach inner frame to the canvas
        self.canvas.create_window((0, 0), window=self.tree_frame, anchor="nw")

        # Treeview (Table)
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=self.columns,
            show="headings",
            selectmode="browse",
        )

        # Configure Columns
        for col in self.columns:
            self.tree.heading(col, text=col, anchor="center")  # Center-align header text
            self.tree.column(col, width=180, minwidth=150, anchor="center", stretch=True)  # Center-align columns

        # Zebra striping (Alternating Row Colors)
        self.tree.tag_configure("evenrow", background="#f1f3f5")
        self.tree.tag_configure("oddrow", background="#ffffff")

        # Packing Treeview inside the inner frame
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Enable dynamic scrolling
        self.tree_frame.update_idletasks()
        make_table_scrollable(self.canvas, self.tree_frame)

    def add_row(self, **kwargs):
        """
        Adds a new row to the table dynamically with alternating colors.
        Args:
            kwargs (dict): Dictionary of column values.
        Returns:
            str: The unique identifier of the added row.
        """
        row_values = [kwargs.get(col, "N/A") for col in self.columns]
        row_count = len(self.tree.get_children())

        tag = "evenrow" if row_count % 2 == 0 else "oddrow"  # Apply zebra-striping
        return self.tree.insert("", "end", values=row_values, tags=(tag,))

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

