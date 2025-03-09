# toolbar.py
import tkinter as tk
from tkinter import ttk
from themes import dark_theme, light_theme  # ✅ Import Centralized Theme


class Toolbar:
    def __init__(self, root, parent_app):
        """Initialize the toolbar."""
        self.root = root
        self.parent_app = parent_app

        # ✅ Use Current Theme from Main App
        theme = self.parent_app.theme

        # ✅ Create Toolbar Frame with Dynamic Theme Support
        self.frame = tk.Frame(self.root, bg=theme["toolbar_bg"])
        self.frame.pack(fill=tk.X, pady=5)

        # ✅ Load Icons (Ensure they are consistent in style)
        self.icons = {"add_url": "➕", "start": "▶️", "stop": "⏸", "delete": "🗑"}

        # ✅ Create Buttons with Icons and Better Spacing
        self.add_url_button = self.create_button(
            f"{self.icons['add_url']} Add URL", self.parent_app.show_add_url_window
        )  # ✅ FIXED
        self.start_button = self.create_button(
            f"{self.icons['start']} Start Download", state="disabled"
        )  # Initially Disabled
        self.stop_button = self.create_button(
            f"{self.icons['stop']} Stop Download", state="disabled"
        )
        self.delete_button = self.create_button(f"{self.icons['delete']} Delete")

        # ✅ Pack Buttons with Increased Padding
        for button in [
            self.add_url_button,
            self.start_button,
            self.stop_button,
            self.delete_button,
        ]:
            button.pack(
                side=tk.LEFT, padx=8, pady=5
            )  # 🔥 Increased padding for better spacing

        # ✅ Apply Initial Theme from Parent App
        self.apply_theme(theme)

    def create_button(self, text, command=None, state="normal"):
        """Creates a styled button with uniform properties."""
        return ttk.Button(
            self.frame, text=text, command=command, state=state, style="Toolbar.TButton"
        )

    def apply_theme(self, theme):
        """Apply the selected theme to the toolbar."""
        self.frame.configure(bg=theme["toolbar_bg"])

        # ✅ Initialize Style System
        style = ttk.Style()
        style.theme_use("clam")  # ✅ Ensure theme is active

        # ✅ Configure Button Styles with Better Disabled Contrast
        style.configure(
            "Toolbar.TButton",
            background=theme["button_bg"],
            foreground=theme["button_fg"],
            padding=(
                12,
                8,
            ),  # 🔥 Increased padding inside buttons for better clickability
            borderwidth=1,
            relief=tk.FLAT,
        )
        style.map(
            "Toolbar.TButton",
            background=[
                ("active", theme["button_active_bg"]),
                ("hover", theme["button_hover_bg"]),
            ],
            foreground=[("disabled", "#7A7A7A")],
        )  # 🔥 Fix: Better visibility for disabled buttons

        # ✅ Ensure All Buttons Have the Updated Theme
        for button in self.frame.winfo_children():
            button.configure(style="Toolbar.TButton")

    def update_theme(self, theme):
        """Update the toolbar's theme dynamically."""
        self.apply_theme(theme)
