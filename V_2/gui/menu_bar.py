import tkinter as tk
from tkinter import ttk, messagebox


class MenuBar:
    def __init__(self, root, app):
        """Initialize the menu bar."""
        self.root = root
        self.app = app  # ✅ Store reference to main app
        self.create_menu_bar()

    def create_menu_bar(self):
        """Creates the menu bar with themed options."""
        self.menu_bar = tk.Menu(self.root)  # ✅ No bg/fg set here!

        # ✅ File Menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Exit", command=self.confirm_exit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # ✅ Downloads Menu
        self.downloads_menu = tk.Menu(self.menu_bar, tearoff=0)

        # ✅ Ensure `download_logic` exists before referencing `stop_all_downloads`
        if hasattr(self.app, "download_logic") and hasattr(
            self.app.download_logic, "stop_all_downloads"
        ):
            self.downloads_menu.add_command(
                label="Stop All", command=self.app.download_logic.stop_all_downloads
            )
        else:
            print("⚠️ Warning: `stop_all_downloads()` is missing or not initialized.")

        self.menu_bar.add_cascade(label="Downloads", menu=self.downloads_menu)

        # ✅ Theme Toggle Menu
        self.theme_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.theme_menu.add_command(
            label="Switch Theme", command=self.app.toggle_theme
        )  # ✅ Simplified
        self.menu_bar.add_cascade(label="Theme", menu=self.theme_menu)

        # ✅ Help Menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_about_dialog)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        # ✅ Apply Menu
        self.root.config(menu=self.menu_bar)

        # ✅ Apply theme dynamically
        self.apply_theme(self.app.theme)

    def apply_theme(self, theme):
        """✅ Applies the current theme to the menu bar and submenus."""
        self.root.option_add("*Menu.background", theme["menu_bg"])
        self.root.option_add("*Menu.foreground", theme["fg"])
        self.root.option_add("*Menu.activeBackground", theme["button_hover_bg"])
        self.root.option_add("*Menu.activeForeground", theme["fg"])

        # ✅ Apply theme to submenus dynamically
        for submenu in [
            self.file_menu,
            self.downloads_menu,
            self.theme_menu,
            self.help_menu,
        ]:
            submenu.configure(
                bg=theme["menu_bg"],
                fg=theme["fg"],
                activebackground=theme["button_hover_bg"],
                activeforeground=theme["fg"],
            )

        # ✅ Force update for full theme application
        self.menu_bar.configure(bg=theme["menu_bg"], fg=theme["fg"])
        self.root.update_idletasks()

    def confirm_exit(self):
        """✅ Shows a confirmation dialog before exiting."""
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit?"):
            self.root.quit()

    def show_about_dialog(self):
        """Displays the About dialog."""
        messagebox.showinfo(
            "About", "Advanced Downloader v1.0\nDeveloped by Serageldin Attia"
        )
