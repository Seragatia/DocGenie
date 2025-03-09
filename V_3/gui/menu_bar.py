# menu_bar.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict

class MenuBar:
    def __init__(self, root: tk.Tk, app: Any) -> None:
        """Initialize the menu bar.

        Args:
            root (tk.Tk): The main application window.
            app (Any): The main application object containing required methods.
        """
        self.root = root
        self.app = app  # Store reference to main app
        self.create_menu_bar()

    def create_menu_bar(self) -> None:
        """Creates the menu bar with themed options."""
        self.menu_bar = tk.Menu(self.root)

        # File Menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Exit", command=self.confirm_exit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Downloads Menu
        self.downloads_menu = tk.Menu(self.menu_bar, tearoff=0)
        if hasattr(self.app, "download_logic") and hasattr(self.app.download_logic, "stop_all_downloads"):
            self.downloads_menu.add_command(
                label="Stop All", command=self.app.download_logic.stop_all_downloads
            )
        else:
            print("⚠️ Warning: `stop_all_downloads()` is missing or not initialized.")
            # Always show a menu item but disable it if not available.
            self.downloads_menu.add_command(label="Stop All (Unavailable)", state="disabled")
        self.menu_bar.add_cascade(label="Downloads", menu=self.downloads_menu)

        # Theme Toggle Menu
        self.theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.theme_menu.add_command(label="Switch Theme", command=self.app.toggle_theme)
        self.menu_bar.add_cascade(label="Theme", menu=self.theme_menu)

        # Help Menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_about_dialog)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        # Apply the menu bar to the root window
        self.root.config(menu=self.menu_bar)
        # Apply theme dynamically
        self.apply_theme(self.app.theme)

    def apply_theme(self, theme: Dict[str, str]) -> None:
        """Applies the current theme to the menu bar and its submenus.

        Args:
            theme (Dict[str, str]): A dictionary containing theme settings (keys: "menu_bg", "fg", "button_hover_bg").
        """
        self.root.option_add("*Menu.background", theme["menu_bg"])
        self.root.option_add("*Menu.foreground", theme["fg"])
        self.root.option_add("*Menu.activeBackground", theme["button_hover_bg"])
        self.root.option_add("*Menu.activeForeground", theme["fg"])

        for submenu in [self.file_menu, self.downloads_menu, self.theme_menu, self.help_menu]:
            submenu.configure(
                bg=theme["menu_bg"],
                fg=theme["fg"],
                activebackground=theme["button_hover_bg"],
                activeforeground=theme["fg"],
            )

        self.menu_bar.configure(bg=theme["menu_bg"], fg=theme["fg"])
        self.root.update_idletasks()

    def confirm_exit(self) -> None:
        """Shows a confirmation dialog before exiting the application."""
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit?"):
            self.root.quit()

    def show_about_dialog(self) -> None:
        """Displays the About dialog."""
        messagebox.showinfo(
            "About", "Advanced Downloader v1.0\nDeveloped by Serageldin Attia"
        )
