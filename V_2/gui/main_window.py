# main_window.py (Indentation Fixed & Updated)
import tkinter as tk
from tkinter import ttk, Toplevel, StringVar, Entry, Checkbutton, IntVar
from gui.toolbar import Toolbar
from gui.download_table import DownloadTable
from gui.menu_bar import MenuBar
from gui.status_label import StatusLabel
# Removed references to old Python modules:
# from modules.download_logic import DownloadLogic
# from modules.add_url_logic import AddURLLogic

from themes import dark_theme, light_theme  # ✅ Centralized theme definitions

class DownloaderApp:
    def __init__(self, root):
        """Initialize the main downloader application window."""
        self.root = root
        self.root.title("Advanced Downloader")

        # ✅ Set Optimized Window Size
        self.root.geometry("1024x600")
        self.root.minsize(800, 500)
        self.root.resizable(True, True)

        # ✅ Theme Mode (Default: Dark)
        self.is_dark_mode = True
        self.theme = dark_theme  # ✅ Initialize theme variable

        # COMMENTED-OUT: Old logic modules no longer used
        # self.download_logic = DownloadLogic(self)
        # self.add_url_logic = AddURLLogic(self)

        # ✅ Create GUI Components
        self.menu_bar = MenuBar(root, self)
        self.toolbar = Toolbar(root, self)
        self.download_table = DownloadTable(root, self)
        self.status_label = StatusLabel(root, self.theme)

        # ✅ Apply Initial Theme AFTER Components are Created
        self.apply_theme()

        # ✅ Apply Custom Styles
        self.apply_custom_styles()

    def toggle_theme(self):
        """Switch between dark and light theme."""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        """Apply the current theme to the entire application."""
        self.theme = dark_theme if self.is_dark_mode else light_theme
        self.root.configure(bg=self.theme["bg"])

        # ✅ Update Components
        self.menu_bar.apply_theme(self.theme)
        self.toolbar.update_theme(self.theme)
        self.download_table.apply_theme(self.theme)
        self.status_label.apply_theme(self.theme)

        # ✅ Redraw UI
        self.root.update_idletasks()

    def show_add_url_window(self):
        add_url_window = Toplevel(self.root)
        add_url_window.title("Enter new address to download")
        add_url_window.geometry("400x280")
        add_url_window.resizable(False, False)
        add_url_window.configure(bg=self.theme["bg"])

        url_var = StringVar()
        use_auth_var = IntVar()
        login_var = StringVar()
        password_var = StringVar()

        form_frame = ttk.Frame(add_url_window, padding=(10, 10))
        form_frame.pack(fill="both", expand=True)

        ttk.Label(
            form_frame,
            text="Address:",
            background=self.theme["bg"],
            foreground=self.theme["fg"]
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ttk.Entry(form_frame, textvariable=url_var, width=40).grid(row=0, column=1, padx=10, pady=5)

        ttk.Checkbutton(form_frame, text="Use authorization", variable=use_auth_var).grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        ttk.Label(form_frame, text="Login:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        ttk.Entry(form_frame, textvariable=login_var, width=25).grid(
            row=2, column=1, padx=10, pady=5, sticky="w"
        )
        ttk.Label(form_frame, text="Password:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        ttk.Entry(form_frame, textvariable=password_var, width=25, show="*").grid(
            row=3, column=1, padx=10, pady=5, sticky="w"
        )

        button_frame = ttk.Frame(add_url_window, padding=(10, 10))
        button_frame.pack(fill="x")

        def on_ok():
            input_url = url_var.get().strip()
            if not input_url:
                print("No URL entered.")
                return

            # EXAMPLE: Call your Rust backend via an HTTP POST to start a download.
            import requests
            data = {
                "id": "some_unique_id",
                "url": input_url,
                "destination": "/some/local/path",  # or gather from user input
                "status": "starting",
                "progress": 0.0
            }
            try:
                response = requests.post("http://127.0.0.1:8080/api/download", json=data)
                if response.status_code == 200:
                    print("Download started:", response.json())
                    self.update_status("Download started!", color="green")
                else:
                    print("Error starting download:", response.text)
                    self.update_status("Error starting download!", color="red")
            except Exception as e:
                print("Failed to call Rust API:", e)
                self.update_status(f"Error: {str(e)}", color="red")

            add_url_window.destroy()

        # Wire the `on_ok` function to the OK button
        ttk.Button(button_frame, text="OK", style="Primary.TButton", command=on_ok).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancel", style="Secondary.TButton", command=add_url_window.destroy).pack(side="right", padx=5)

    def apply_custom_styles(self):
        """Applies consistent button styles."""
        style = ttk.Style()
        style.theme_use("clam")

        # ✅ Primary Button (Green for Actions)
        style.configure("Primary.TButton", background="#4CAF50", foreground="white", padding=(10, 5))
        style.map("Primary.TButton", background=[("active", "#45A049"), ("hover", "#66BB6A")])

        # ✅ Secondary Button (Gray for Neutral Actions)
        style.configure("Secondary.TButton", background="#757575", foreground="white", padding=(10, 5))
        style.map("Secondary.TButton", background=[("active", "#616161"), ("hover", "#9E9E9E")])

    def update_status(self, message, color="black"):
        """Updates the status message in the status label."""
        self.status_label.update_status(message, color)


if __name__ == "__main__":
    root = tk.Tk()
    app = DownloaderApp(root)
    root.mainloop()
