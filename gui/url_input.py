import tkinter as tk
from tkinter import filedialog

class URLInput:
    def __init__(self, root, app):
        self.frame = tk.Frame(root)
        self.frame.pack(pady=10, fill=tk.X)

        tk.Label(self.frame, text="Enter URL:").grid(row=0, column=0, padx=5)
        self.url_entry = tk.Entry(self.frame, width=60)
        self.url_entry.grid(row=0, column=1, padx=5)

        tk.Label(self.frame, text="Output Folder:").grid(row=1, column=0, padx=5)
        self.folder_entry = tk.Entry(self.frame, width=40)
        self.folder_entry.grid(row=1, column=1, padx=5)
        tk.Button(self.frame, text="Browse", command=self.browse_folder).grid(row=1, column=2, padx=5)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)

    def get_url(self):
        return self.url_entry.get()

    def get_output_folder(self):
        return self.folder_entry.get()
