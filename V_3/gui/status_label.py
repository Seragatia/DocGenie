import tkinter as tk
from typing import Dict, Optional

class StatusLabel:
    def __init__(self, root: tk.Widget, theme: Dict[str, str]) -> None:
        """
        Initialize the status label with the given theme.

        Args:
            root (tk.Widget): The parent widget.
            theme (Dict[str, str]): A dictionary with theme settings. Expected keys include "fg" and "bg".
        """
        self.theme: Dict[str, str] = theme
        self.label: tk.Label = tk.Label(
            root,
            text="Welcome to the Advanced Downloader!",
            fg=theme.get("fg", "black"),
            bg=theme.get("bg", "white"),
        )
        self.label.pack(pady=10, fill=tk.X)

    def update_status(self, message: str, color: Optional[str] = None) -> None:
        """
        Update the status message with an optional text color.

        Args:
            message (str): The new status message.
            color (Optional[str], optional): The text color to use. Defaults to the theme's foreground color.
        """
        fg_color = color if color is not None else self.theme.get("fg", "black")
        self.label.config(text=message, fg=fg_color)

    def apply_theme(self, theme: Dict[str, str]) -> None:
        """
        Dynamically update the theme for the status label.

        Args:
            theme (Dict[str, str]): A dictionary with new theme settings.
        """
        self.theme = theme
        self.label.config(bg=theme.get("bg", "white"), fg=theme.get("fg", "black"))
