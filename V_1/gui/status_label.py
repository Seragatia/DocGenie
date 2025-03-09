# status_label.py
import tkinter as tk


class StatusLabel:
    def __init__(self, root, theme):
        """Initialize the status label with the correct theme."""
        self.theme = theme  # ✅ Store theme reference
        self.label = tk.Label(
            root,
            text="Welcome to the Advanced Downloader!",
            fg=theme["fg"],
            bg=theme["bg"],
        )
        self.label.pack(pady=10, fill=tk.X)

    def update_status(self, message, color=None):
        """Update the status message with optional color."""
        fg_color = color if color else self.theme["fg"]  # ✅ Default to theme fg color
        self.label.config(text=message, fg=fg_color)

    def apply_theme(self, theme):
        """Dynamically update the theme for the status label."""
        self.theme = theme  # ✅ Update stored theme
        self.label.config(bg=theme["bg"], fg=theme["fg"])  # ✅ Apply new theme colors
