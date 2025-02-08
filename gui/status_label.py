import tkinter as tk


class StatusLabel:
    def __init__(self, root):
        self.label = tk.Label(root, text="Welcome to the Advanced Downloader!", fg="blue")
        self.label.pack(pady=10)

    def update_status(self, message, color="blue"):
        self.label.config(text=message, fg=color)
