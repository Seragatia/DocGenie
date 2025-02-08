import tkinter as tk
from tkinter import messagebox

class MenuBar:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.create_menu_bar()

    def create_menu_bar(self):
        """Create a menu bar for the application."""
        menu_bar = tk.Menu(self.root)

        # File Menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Add URL", command=self.app.download_logic.start_download)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Downloads Menu
        downloads_menu = tk.Menu(menu_bar, tearoff=0)
        downloads_menu.add_command(label="Pause All", state=tk.DISABLED)  # Placeholder
        downloads_menu.add_command(label="Stop All", command=self.app.download_logic.stop_all_downloads)
        downloads_menu.add_separator()
        downloads_menu.add_command(label="Delete All Completed", command=self.app.download_logic.delete_completed_downloads)
        downloads_menu.add_separator()
        menu_bar.add_cascade(label="Downloads", menu=downloads_menu)

        # Help Menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menu_bar)

    def show_about_dialog(self):
        """Display the About dialog."""
        messagebox.showinfo("About", "Advanced Downloader v1.0\nDeveloped by [Your Name]")
