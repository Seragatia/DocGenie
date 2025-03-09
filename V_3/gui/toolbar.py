import tkinter as tk
from tkinter import ttk
from typing import Any, Dict
from themes import dark_theme, light_theme  # Centralized theme definitions


class Toolbar:
    def __init__(self, root: tk.Widget, parent_app: Any) -> None:
        """
        Initialize the toolbar.

        Args:
            root (tk.Widget): The parent widget.
            parent_app (Any): The main application instance holding the current theme and methods.
        """
        self.root = root
        self.parent_app = parent_app

        # Use current theme from main app
        theme: Dict[str, str] = self.parent_app.theme

        # Create Toolbar Frame with dynamic theme support
        self.frame: tk.Frame = tk.Frame(self.root, bg=theme.get("toolbar_bg", "#CCCCCC"))
        self.frame.pack(fill=tk.X, pady=5)

        # Load Icons (ensure consistent style)
        self.icons = {"add_url": "➕", "start": "▶️", "stop": "⏸", "delete": "🗑"}

        # Create Buttons with icons and better spacing
        self.add_url_button = self.create_button(
            f"{self.icons['add_url']} Add URL", self.parent_app.show_add_url_window
        )
        self.start_button = self.create_button(
            f"{self.icons['start']} Start Download", state="disabled"
        )
        self.stop_button = self.create_button(
            f"{self.icons['stop']} Stop Download", state="disabled"
        )
        self.delete_button = self.create_button(f"{self.icons['delete']} Delete")

        # Pack buttons with increased padding for better spacing
        for button in [
            self.add_url_button,
            self.start_button,
            self.stop_button,
            self.delete_button,
        ]:
            button.pack(side=tk.LEFT, padx=8, pady=5)

        # Apply initial theme from parent app
        self.apply_theme(theme)

    def create_button(self, text: str, command: Any = None, state: str = "normal") -> ttk.Button:
        """
        Creates a styled button with uniform properties.

        Args:
            text (str): The button text.
            command (Optional[Any]): The function to be called when the button is pressed.
            state (str): The initial state of the button.

        Returns:
            ttk.Button: The created button widget.
        """
        return ttk.Button(self.frame, text=text, command=command, state=state, style="Toolbar.TButton")

    def apply_theme(self, theme: Dict[str, str]) -> None:
        """
        Apply the selected theme to the toolbar.

        Args:
            theme (Dict[str, str]): A dictionary containing theme settings.
                                    Expected keys: "toolbar_bg", "button_bg", "button_fg",
                                    "button_active_bg", "button_hover_bg".
        """
        self.frame.configure(bg=theme.get("toolbar_bg", "#CCCCCC"))

        # Initialize Style System
        style = ttk.Style()
        style.theme_use("clam")  # Ensure theme is active

        # Configure button styles with improved padding and disabled contrast
        style.configure(
            "Toolbar.TButton",
            background=theme.get("button_bg", "#EEEEEE"),
            foreground=theme.get("button_fg", "#000000"),
            padding=(12, 8),  # Increased padding for better clickability
            borderwidth=1,
            relief=tk.FLAT,
        )
        style.map(
            "Toolbar.TButton",
            background=[
                ("active", theme.get("button_active_bg", "#DDDDDD")),
                ("hover", theme.get("button_hover_bg", "#BBBBBB")),
            ],
            foreground=[("disabled", "#7A7A7A")],
        )

        # Ensure all buttons in the toolbar adopt the updated style
        for button in self.frame.winfo_children():
            button.configure(style="Toolbar.TButton")

    def update_theme(self, theme: Dict[str, str]) -> None:
        """
        Update the toolbar's theme dynamically.

        Args:
            theme (Dict[str, str]): A dictionary with the new theme settings.
        """
        self.apply_theme(theme)
